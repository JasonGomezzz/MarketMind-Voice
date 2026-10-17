"""
Reintentos seguros: recuperar el id de un post ya publicado y retomar una
publicación atascada sin duplicarla. La Graph API se simula.
"""

from datetime import datetime, timedelta
from datetime import timezone as dt_timezone
from unittest.mock import patch

import pytest
from django.utils import timezone

from apps.authentication.models import User
from apps.campaigns.models import Campaign, CampaignStatus
from apps.social.models import PublicacionEstado, Publication, RedSocial
from services import meta_graph, metrics_service, publication_service

from .datos import cliente_api, conexion, publicacion

RESULTADO = meta_graph.ResultadoPublicacion(externo_id="media-1", permalink="https://www.instagram.com/p/1/")


def reintentar(user: User, p: Publication):
    return cliente_api(user).post(f"/api/social/publications/{p.id}/publish/")


@pytest.mark.django_db
class TestContenedorYaPublicado:
    """Bug a: el contenedor quedó PUBLISHED tras un fallo ambiguo y la publicación quedaba sin id."""

    @pytest.fixture
    def fallida(self, campana, cliente) -> Publication:
        return publicacion(campana, conexion(cliente), estado=PublicacionEstado.FALLIDO, intentos=1,
                           contenedor_id="cont-9", error="Meta no respondió a tiempo.")

    def test_sin_coincidencia_queda_publicado_con_aviso_honesto(self, fallida, user_marketero):
        with patch.object(meta_graph, "estado_contenedor", return_value="PUBLISHED"), \
                patch.object(meta_graph, "buscar_publicacion_instagram", return_value=None), \
                patch.object(meta_graph, "publicar_instagram") as publicar:
            response = reintentar(user_marketero, fallida)
        publicar.assert_not_called()
        assert response.status_code == 200
        fallida.refresh_from_db()
        assert fallida.estado == PublicacionEstado.PUBLICADO and fallida.externo_id == ""
        assert "no se pudo identificar" in fallida.error
        with pytest.raises(metrics_service.MetricasNoDisponibles, match="identificar"):
            metrics_service.refrescar_metricas(fallida)

    def test_si_la_busqueda_falla_tampoco_republica(self, fallida, user_marketero):
        with patch.object(meta_graph, "estado_contenedor", return_value="PUBLISHED"), \
                patch.object(meta_graph, "buscar_publicacion_instagram", side_effect=meta_graph.MetaError("límite")), \
                patch.object(meta_graph, "publicar_instagram") as publicar:
            reintentar(user_marketero, fallida)
        publicar.assert_not_called()
        fallida.refresh_from_db()
        assert fallida.estado == PublicacionEstado.PUBLICADO and "no se pudo identificar" in fallida.error

    def test_busca_desde_que_se_programo_y_excluye_posts_de_otras_publicaciones(
        self, fallida, campana, cliente, user_marketero
    ):
        otra = Campaign.objects.create(
            titulo="Otra", cliente_nombre="Café", cliente_email=cliente.email, industria="x", tono="casual",
            plataforma="instagram", prompt="prompt suficientemente largo", estado=CampaignStatus.APROBADO,
            marketero=user_marketero,
        )
        publicacion(otra, fallida.conexion, estado=PublicacionEstado.PUBLICADO, externo_id="media-viejo")
        with patch.object(meta_graph, "estado_contenedor", return_value="PUBLISHED"), \
                patch.object(meta_graph, "buscar_publicacion_instagram", return_value=RESULTADO) as buscar:
            reintentar(user_marketero, fallida)
        ig_id, _, caption, desde, excluir = buscar.call_args.args
        assert (ig_id, caption) == ("ig-1", "Copy aprobado")
        assert desde <= fallida.fecha_creacion
        assert list(excluir) == ["media-viejo"]

    def test_contenedor_listo_se_publica_sin_crear_otro(self, fallida, user_marketero):
        with patch.object(meta_graph, "estado_contenedor", return_value="FINISHED"), \
                patch.object(meta_graph, "publicar_contenedor", return_value=RESULTADO) as publicar_contenedor, \
                patch.object(meta_graph, "publicar_instagram") as publicar:
            reintentar(user_marketero, fallida)
        publicar.assert_not_called()
        assert publicar_contenedor.call_args.args == ("ig-1", "token-de-pagina", "cont-9")
        fallida.refresh_from_db()
        assert fallida.estado == PublicacionEstado.PUBLICADO and fallida.externo_id == "media-1"

    def test_contenedor_con_error_crea_uno_nuevo(self, fallida, user_marketero):
        with patch.object(meta_graph, "estado_contenedor", return_value="ERROR"), \
                patch.object(meta_graph, "publicar_instagram", return_value=RESULTADO) as publicar:
            reintentar(user_marketero, fallida)
        publicar.assert_called_once()


@pytest.mark.django_db
class TestPublicacionAtascada:
    """Bug b: si el proceso moría quedaba 'publicando' para siempre."""

    def atascada(self, campana, con, minutos: int, **extra) -> Publication:
        datos = {"intentos": 1, **extra}
        return publicacion(campana, con, estado=PublicacionEstado.PUBLICANDO,
                           publicando_desde=timezone.now() - timedelta(minutes=minutos), **datos)

    def test_reciente_no_se_puede_reintentar(self, campana, cliente, user_marketero):
        p = self.atascada(campana, conexion(cliente), minutos=1)
        with patch.object(meta_graph, "publicar_instagram") as publicar:
            response = reintentar(user_marketero, p)
        assert response.status_code == 409
        assert "se está procesando" in response.data["message"]
        publicar.assert_not_called()

    def test_vieja_con_contenedor_publicado_se_recupera_sin_duplicar(self, campana, cliente, user_marketero):
        p = self.atascada(campana, conexion(cliente), minutos=6, contenedor_id="cont-7", intentos=3)
        with patch.object(meta_graph, "estado_contenedor", return_value="PUBLISHED"), \
                patch.object(meta_graph, "buscar_publicacion_instagram", return_value=RESULTADO), \
                patch.object(meta_graph, "publicar_instagram") as publicar:
            response = reintentar(user_marketero, p)
        assert response.status_code == 200
        publicar.assert_not_called()
        p.refresh_from_db()
        assert (p.estado, p.externo_id) == (PublicacionEstado.PUBLICADO, "media-1")

    def test_vieja_sin_contenedor_ni_post_se_publica_una_vez(self, campana, cliente, user_marketero):
        p = self.atascada(campana, conexion(cliente), minutos=6)
        with patch.object(meta_graph, "buscar_publicacion_instagram", return_value=None) as buscar, \
                patch.object(meta_graph, "publicar_instagram", return_value=RESULTADO) as publicar:
            reintentar(user_marketero, p)
        buscar.assert_called_once()
        publicar.assert_called_once()
        p.refresh_from_db()
        assert p.estado == PublicacionEstado.PUBLICADO and p.intentos == 2

    def test_facebook_vieja_que_ya_salio_no_se_repite(self, campana, cliente, user_marketero):
        con = conexion(cliente, red=RedSocial.FACEBOOK, cuenta_id="page-1", cuenta_nombre="Café")
        p = self.atascada(campana, con, minutos=10)
        post = meta_graph.ResultadoPublicacion(externo_id="page-1_55", permalink="https://facebook.com/55")
        with patch.object(meta_graph, "buscar_publicacion_facebook", return_value=post) as buscar, \
                patch.object(meta_graph, "publicar_facebook") as publicar:
            reintentar(user_marketero, p)
        assert buscar.call_args.args[0] == "page-1"
        publicar.assert_not_called()
        p.refresh_from_db()
        assert (p.estado, p.externo_id) == (PublicacionEstado.PUBLICADO, "page-1_55")

    def test_el_aviso_de_aprobacion_no_toca_una_publicando(self, campana, cliente):
        p = self.atascada(campana, conexion(cliente), minutos=60)
        resumen = publication_service.publicar_campana_aprobada(campana.id)
        assert resumen.publicadas == 0
        p.refresh_from_db()
        assert p.estado == PublicacionEstado.PUBLICANDO

    def test_el_contenedor_se_guarda_antes_de_publicar(self, campana, cliente):
        """Si el proceso muere tras crear el contenedor, el reintento lo encuentra en la base."""
        p = publicacion(campana, conexion(cliente))
        guardado = {}

        def graph(metodo, ruta, **params):
            if ruta == "ig-1/media":
                return {"id": "cont-nuevo"}
            if params.get("fields") == "status_code":
                return {"status_code": "FINISHED"}
            guardado["contenedor"] = Publication.objects.get(pk=p.pk).contenedor_id
            raise meta_graph.MetaError("proceso interrumpido")

        with patch.object(meta_graph, "_graph", side_effect=graph):
            publication_service.publicar_campana_aprobada(campana.id)
        assert guardado["contenedor"] == "cont-nuevo"
        assert Publication.objects.get(pk=p.pk).publicando_desde is not None

    def test_publicacion_atascada_usa_la_marca_de_inicio(self, campana, cliente):
        p = self.atascada(campana, conexion(cliente), minutos=6)
        assert publication_service.publicacion_atascada(p)
        p.publicando_desde = timezone.now()
        assert not publication_service.publicacion_atascada(p)
        p.estado = PublicacionEstado.FALLIDO
        assert not publication_service.publicacion_atascada(p)


class TestBusquedaEnMeta:
    desde = datetime(2026, 10, 16, 10, 0, tzinfo=dt_timezone.utc)

    def test_instagram_elige_el_unico_media_con_el_caption(self):
        data = {"data": [
            {"id": "m-viejo", "caption": "Copy aprobado", "timestamp": "2026-10-15T10:00:00+0000"},
            {"id": "m-otro", "caption": "Otro texto", "timestamp": "2026-10-16T10:05:00+0000"},
            {"id": "m-usado", "caption": "Copy aprobado", "timestamp": "2026-10-16T10:06:00+0000"},
            {"id": "m-1", "caption": "Copy aprobado ", "timestamp": "2026-10-16T10:07:00+0000",
             "permalink": "https://www.instagram.com/p/1/"},
        ]}
        with patch.object(meta_graph, "_graph", return_value=data) as graph:
            resultado = meta_graph.buscar_publicacion_instagram("ig-1", "tok", "Copy aprobado", self.desde,
                                                                 excluir=["m-usado"])
        assert (resultado.externo_id, resultado.permalink) == ("m-1", "https://www.instagram.com/p/1/")
        assert graph.call_args.args == ("GET", "ig-1/media")
        assert graph.call_args.kwargs["since"] == int(self.desde.timestamp())

    def test_dos_coincidencias_no_adivina(self):
        data = {"data": [
            {"id": "a", "caption": "Copy", "timestamp": "2026-10-16T10:05:00+0000"},
            {"id": "b", "caption": "Copy", "timestamp": "2026-10-16T10:06:00+0000"},
        ]}
        with patch.object(meta_graph, "_graph", return_value=data):
            assert meta_graph.buscar_publicacion_instagram("ig-1", "tok", "Copy", self.desde) is None

    def test_facebook_busca_en_el_feed_por_mensaje(self):
        data = {"data": [{"id": "page-1_9", "message": "Copy", "created_time": "2026-10-16T11:00:00+0000",
                          "permalink_url": "https://facebook.com/9"}]}
        with patch.object(meta_graph, "_graph", return_value=data) as graph:
            resultado = meta_graph.buscar_publicacion_facebook("page-1", "tok", "Copy", self.desde)
        assert resultado.externo_id == "page-1_9"
        assert graph.call_args.args == ("GET", "page-1/feed")

    def test_si_falla_leer_el_enlace_igual_cuenta_como_publicado(self):
        def graph(metodo, ruta, **params):
            if ruta == "ig-1/media_publish":
                return {"id": "media-1"}
            if params.get("fields") == "status_code":
                return {"status_code": "FINISHED"}
            raise meta_graph.MetaError("permalink no disponible")

        with patch.object(meta_graph, "_graph", side_effect=graph):
            resultado = meta_graph.publicar_contenedor("ig-1", "tok", "cont-1", esperar=lambda s: None)
        assert (resultado.externo_id, resultado.permalink, resultado.contenedor_id) == ("media-1", "", "cont-1")
