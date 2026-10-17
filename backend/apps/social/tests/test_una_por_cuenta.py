"""Cliente y marketero con la misma cuenta de Meta conectada: una sola publicación, un solo post."""

import importlib
from unittest.mock import patch

import pytest
from django.apps import apps as registro_apps

from apps.campaigns.models import Campaign, CampaignStatus
from apps.social.models import PublicacionEstado, Publication, RedSocial
from services import publication_service

from .datos import cliente_api, conexion, publicacion


@pytest.mark.django_db
class TestUnaPorCuenta:
    def test_misma_cuenta_de_cliente_y_marketero_programa_una_sola(self, campana, cliente, user_marketero):
        del_marketero = conexion(user_marketero)
        del_cliente = conexion(cliente)
        Campaign.objects.filter(pk=campana.pk).update(estado=CampaignStatus.GENERADO)
        with patch("apps.campaigns.views.notify_campaign_submitted"):
            response = cliente_api(user_marketero).post(
                f"/api/campaigns/{campana.id}/submit/", {"destinos": [del_marketero.id, del_cliente.id]},
                format="json",
            )
        assert response.status_code == 200
        assert len(response.data["data"]["destinos"]) == 1
        unica = Publication.objects.get(campaign=campana)
        assert unica.conexion_id == del_cliente.id  # gana la del dueño
        assert unica.cuenta_id == "ig-1"

    def test_reenviar_reutiliza_la_publicacion_de_esa_cuenta(self, campana, cliente, user_marketero):
        del_cliente = conexion(cliente)
        del_marketero = conexion(user_marketero)
        primera = publication_service.programar_publicaciones(campana, [del_cliente.id], user_marketero)
        segunda = publication_service.programar_publicaciones(campana, [del_marketero.id], user_marketero)
        assert [p.pk for p in primera] == [p.pk for p in segunda]
        assert Publication.objects.filter(campaign=campana).count() == 1

    def test_cuentas_distintas_siguen_siendo_dos(self, campana, cliente, user_marketero):
        ig = conexion(cliente)
        fb = conexion(cliente, red=RedSocial.FACEBOOK, cuenta_id="page-1", cuenta_nombre="Café")
        assert len(publication_service.programar_publicaciones(campana, [ig.id, fb.id], user_marketero)) == 2

    def test_destinos_ofrece_la_cuenta_una_vez(self, cliente, user_marketero):
        conexion(user_marketero, cuenta_nombre="@cafe (agencia)")
        conexion(cliente)
        data = cliente_api(user_marketero).get(
            "/api/social/connections/destinos/", {"cliente_email": cliente.email}
        ).data["data"]["conexiones"]
        assert [(c["cuenta_nombre"], c["propietario_email"]) for c in data] == [("@cafe.aurora", cliente.email)]

    def test_migracion_deja_una_titular_y_cancela_la_duplicada_pendiente(self, campana, cliente, user_marketero):
        del_cliente, del_marketero = conexion(cliente), conexion(user_marketero)
        publicada = publicacion(campana, del_marketero, cuenta_id="", estado=PublicacionEstado.PUBLICADO)
        pendiente = publicacion(campana, del_cliente, cuenta_id="")
        migracion = importlib.import_module("apps.social.migrations.0005_rellenar_cuenta_publicacion")
        migracion.rellenar(registro_apps, None)
        publicada.refresh_from_db()
        pendiente.refresh_from_db()
        assert publicada.cuenta_id == "ig-1" and publicada.estado == PublicacionEstado.PUBLICADO
        assert pendiente.cuenta_id == "" and pendiente.estado == PublicacionEstado.CANCELADO
