"""OAuth de Meta: state de un solo uso ligado al usuario y canje solo con su JWT. La Graph API se simula."""

import hashlib
from datetime import timedelta
from unittest.mock import patch
from urllib.parse import parse_qs, urlparse

import pytest
from django.utils import timezone
from rest_framework.test import APIClient

from apps.authentication.models import User, UserRole
from apps.social import oauth
from apps.social.models import ConexionEstado, OAuthAutorizacion, RedSocial, SocialConnection
from services import meta_graph
from services.social_tokens import cifrar, descifrar

CONNECT = "/api/social/meta/connect/"
CALLBACK = "/api/social/meta/callback/"
COMPLETE = "/api/social/meta/complete/"

PAGINAS = [{
    "id": "page-1", "name": "Café Aurora", "access_token": "EAAG-pagina",
    "instagram_business_account": {"id": "ig-1", "username": "cafe.aurora"},
}]


def cliente_api(user: User) -> APIClient:
    client = APIClient()
    client.force_authenticate(user=user)
    return client


def iniciar(user: User) -> str:
    """Pide la URL de Meta como lo hace el frontend y devuelve el state que viaja en ella."""
    url = urlparse(cliente_api(user).get(CONNECT).data["data"]["url"])
    return parse_qs(url.query)["state"][0]


def fragmento(response) -> dict[str, str]:
    destino = urlparse(response["Location"])
    return {k: v[0] for k, v in parse_qs(destino.fragment).items()}


@pytest.fixture
def otro_cliente(db) -> User:
    return User.objects.create_user(email="atacante@test.com", password="Test1234!", nombre="Atacante",
                                    rol=UserRole.CLIENTE)


@pytest.mark.django_db
class TestIniciar:
    def test_marketero_obtiene_url_con_state_aleatorio_y_permisos(self, api_client, user_marketero):
        response = api_client.get(CONNECT)
        assert response.status_code == 200
        url = urlparse(response.data["data"]["url"])
        params = parse_qs(url.query)
        assert url.netloc == "www.facebook.com"
        assert params["client_id"] == ["test-app"]
        scope = params["scope"][0].split(",")
        assert {"instagram_content_publish", "read_insights", "pages_read_user_content"} <= set(scope)

        state = params["state"][0]
        autorizacion = OAuthAutorizacion.objects.get(usuario=user_marketero)
        # Solo se guarda el hash: el state en claro no está en la base.
        assert autorizacion.state_hash == hashlib.sha256(state.encode()).hexdigest() != state
        assert autorizacion.token_version == user_marketero.token_version
        assert autorizacion.usada_at is None
        assert timedelta(minutes=9) < autorizacion.expira_at - timezone.now() <= timedelta(minutes=10)
        assert params["redirect_uri"] == [autorizacion.redirect_uri]

    def test_cada_intento_tiene_su_propio_state(self, cliente):
        assert iniciar(cliente) != iniciar(cliente)
        assert OAuthAutorizacion.objects.filter(usuario=cliente).count() == 2

    def test_borra_autorizaciones_viejas_del_usuario(self, cliente):
        iniciar(cliente)
        OAuthAutorizacion.objects.update(expira_at=timezone.now() - timedelta(days=2))
        iniciar(cliente)
        assert OAuthAutorizacion.objects.filter(usuario=cliente).count() == 1

    def test_con_configuracion_de_login_para_empresas_usa_config_id(self, api_client, settings):
        settings.META_LOGIN_CONFIG_ID = "cfg-123"
        params = parse_qs(urlparse(api_client.get(CONNECT).data["data"]["url"]).query)
        assert params["config_id"] == ["cfg-123"]
        assert "scope" not in params

    def test_superadmin_no_conecta(self, superadmin_client):
        assert superadmin_client.get(CONNECT).status_code == 403
        assert not OAuthAutorizacion.objects.exists()

    def test_sin_app_configurada_503(self, api_client, settings):
        settings.META_APP_ID = ""
        assert api_client.get(CONNECT).status_code == 503


@pytest.mark.django_db
class TestCallback:
    def test_no_canjea_y_pasa_code_y_state_en_el_fragmento(self, cliente):
        state = iniciar(cliente)
        with patch.object(meta_graph, "canjear_codigo") as canjear:
            response = APIClient().get(CALLBACK, {"code": "abc", "state": state})
        canjear.assert_not_called()
        assert response.status_code == 302
        destino = urlparse(response["Location"])
        assert f"{destino.scheme}://{destino.netloc}{destino.path}" == "http://frontend.test/redes/meta-retorno"
        assert destino.query == ""  # nada en la query: el fragmento no llega a servidores
        assert fragmento(response) == {"code": "abc", "state": state}
        assert response["Cache-Control"] == "no-store"
        assert not SocialConnection.objects.exists()
        assert OAuthAutorizacion.objects.get().usada_at is None

    def test_state_desconocido(self, db):
        response = APIClient().get(CALLBACK, {"code": "abc", "state": "inventado"})
        assert fragmento(response) == {"error": "sesion"}

    def test_state_caducado(self, cliente):
        state = iniciar(cliente)
        OAuthAutorizacion.objects.update(expira_at=timezone.now() - timedelta(seconds=1))
        assert fragmento(APIClient().get(CALLBACK, {"code": "abc", "state": state})) == {"error": "sesion"}

    def test_state_ya_usado(self, cliente):
        state = iniciar(cliente)
        OAuthAutorizacion.objects.update(usada_at=timezone.now())
        assert fragmento(APIClient().get(CALLBACK, {"code": "abc", "state": state})) == {"error": "sesion"}

    def test_sin_codigo(self, cliente):
        state = iniciar(cliente)
        assert fragmento(APIClient().get(CALLBACK, {"state": state})) == {"error": "sin_codigo"}

    def test_cancelado_en_meta_invalida_el_state(self, cliente):
        state = iniciar(cliente)
        response = APIClient().get(CALLBACK, {"error": "access_denied", "state": state})
        assert fragmento(response) == {"error": "cancelado"}
        assert OAuthAutorizacion.objects.get().usada_at is not None


@pytest.mark.django_db
class TestCompletar:
    def completar(self, user: User, state: str, code: str = "abc"):
        return cliente_api(user).post(COMPLETE, {"code": code, "state": state}, format="json")

    def test_exito_guarda_pagina_e_instagram_cifrados_y_marca_usado(self, cliente):
        state = iniciar(cliente)
        with patch.object(meta_graph, "canjear_codigo", return_value="user-token") as canjear, \
                patch.object(meta_graph, "paginas_con_instagram", return_value=PAGINAS):
            response = self.completar(cliente, state)

        assert response.status_code == 200
        assert response.data["data"]["conectadas"] == 2
        autorizacion = OAuthAutorizacion.objects.get()
        # Mismo redirect_uri que el diálogo de Meta.
        canjear.assert_called_once_with("abc", autorizacion.redirect_uri)
        assert autorizacion.usada_at is not None
        conexiones = SocialConnection.objects.filter(usuario=cliente).order_by("red")
        assert [(c.red, c.cuenta_nombre) for c in conexiones] == [
            ("facebook", "Café Aurora"), ("instagram", "@cafe.aurora"),
        ]
        assert all("EAAG" not in c.token_cifrado for c in conexiones)
        assert descifrar(conexiones[1].token_cifrado) == "EAAG-pagina"
        assert all("token" not in clave for c in response.data["data"]["conexiones"] for clave in c)

    def test_state_ajeno_no_vincula_la_cuenta(self, cliente, otro_cliente):
        """El atacante inicia el flujo y hace que la víctima lo termine: se rechaza sin canjear."""
        state_del_atacante = iniciar(otro_cliente)
        with patch.object(meta_graph, "canjear_codigo") as canjear:
            response = self.completar(cliente, state_del_atacante)
        assert response.status_code == 403
        assert response.data["data"]["motivo"] == "ajena"
        assert "otra cuenta" in response.data["message"]
        canjear.assert_not_called()
        assert not SocialConnection.objects.exists()
        assert OAuthAutorizacion.objects.get().usada_at is None

    def test_state_reutilizado(self, cliente):
        state = iniciar(cliente)
        with patch.object(meta_graph, "canjear_codigo", return_value="t") as canjear, \
                patch.object(meta_graph, "paginas_con_instagram", return_value=PAGINAS):
            assert self.completar(cliente, state).status_code == 200
            segunda = self.completar(cliente, state)
        assert segunda.status_code == 409
        assert segunda.data["data"]["motivo"] == "usada"
        assert canjear.call_count == 1

    def test_state_caducado(self, cliente):
        state = iniciar(cliente)
        OAuthAutorizacion.objects.update(expira_at=timezone.now() - timedelta(seconds=1))
        with patch.object(meta_graph, "canjear_codigo") as canjear:
            response = self.completar(cliente, state)
        assert response.status_code == 400
        assert response.data["data"]["motivo"] == "caducada"
        assert "caducó" in response.data["message"]
        canjear.assert_not_called()

    def test_token_version_cambiado(self, cliente):
        state = iniciar(cliente)
        User.objects.filter(pk=cliente.pk).update(token_version=cliente.token_version + 1)
        cliente.refresh_from_db()
        with patch.object(meta_graph, "canjear_codigo") as canjear:
            response = self.completar(cliente, state)
        assert response.status_code == 403
        assert response.data["data"]["motivo"] == "sesion"
        canjear.assert_not_called()

    def test_state_desconocido(self, cliente):
        response = self.completar(cliente, "inventado")
        assert response.status_code == 400
        assert response.data["data"]["motivo"] == "desconocida"

    @pytest.mark.parametrize("datos", [{}, {"code": "abc"}, {"state": "x"}, {"code": 1, "state": "x"},
                                       {"code": "a" * 5000, "state": "x"}])
    def test_datos_incompletos_400(self, cliente, datos):
        response = cliente_api(cliente).post(COMPLETE, datos, format="json")
        assert response.status_code == 400
        assert "Meta" in response.data["message"]

    def test_requiere_sesion(self, cliente):
        state = iniciar(cliente)
        response = APIClient().post(COMPLETE, {"code": "abc", "state": state}, format="json")
        assert response.status_code == 401

    def test_superadmin_403(self, superadmin):
        assert self.completar(superadmin, "x").status_code == 403

    def test_error_de_meta_502_y_el_state_no_se_reutiliza(self, cliente):
        state = iniciar(cliente)
        with patch.object(meta_graph, "canjear_codigo", side_effect=meta_graph.MetaError("code vencido")):
            response = self.completar(cliente, state)
        assert response.status_code == 502
        assert "Vuelve a conectar" in response.data["message"]
        assert self.completar(cliente, state).status_code == 409

    def test_sin_paginas_422(self, cliente):
        state = iniciar(cliente)
        with patch.object(meta_graph, "canjear_codigo", return_value="t"), \
                patch.object(meta_graph, "paginas_con_instagram", return_value=[]):
            response = self.completar(cliente, state)
        assert response.status_code == 422
        assert "página" in response.data["message"]

    def test_reconectar_actualiza_sin_duplicar(self, cliente):
        SocialConnection.objects.create(
            usuario=cliente, red=RedSocial.INSTAGRAM, cuenta_id="ig-1", cuenta_nombre="@viejo",
            pagina_id="page-1", token_cifrado=cifrar("viejo"), estado=ConexionEstado.DESCONECTADA,
        )
        state = iniciar(cliente)
        with patch.object(meta_graph, "canjear_codigo", return_value="t"), \
                patch.object(meta_graph, "paginas_con_instagram", return_value=PAGINAS):
            self.completar(cliente, state)
        ig = SocialConnection.objects.get(usuario=cliente, red="instagram")
        assert ig.estado == ConexionEstado.ACTIVA and ig.cuenta_nombre == "@cafe.aurora"
        assert SocialConnection.objects.filter(usuario=cliente, red="instagram").count() == 1

    def test_reclamar_es_condicional(self, cliente):
        """Si otra petición marcó el state entre la lectura y el UPDATE, esta no lo canjea."""
        state = iniciar(cliente)
        filtro_original = OAuthAutorizacion.objects.filter

        def filtro_con_carrera(*args, **kwargs):
            if "usada_at__isnull" in kwargs and "pk" in kwargs:
                OAuthAutorizacion.objects.update(usada_at=timezone.now())
            return filtro_original(*args, **kwargs)

        with patch.object(OAuthAutorizacion.objects, "filter", side_effect=filtro_con_carrera):
            with pytest.raises(oauth.AutorizacionInvalida) as exc:
                oauth.reclamar(cliente, state)
        assert exc.value.motivo == "usada"
