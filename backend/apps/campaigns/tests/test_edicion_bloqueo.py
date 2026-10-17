"""Bloqueo de edición por estado y versión optimista (adaptado de la rama de Piero)."""

from unittest.mock import patch

import pytest

from apps.campaigns.models import Campaign, CampaignStatus, CampaignVersion

pytestmark = pytest.mark.django_db

EDITABLES = [CampaignStatus.BORRADOR, CampaignStatus.GENERADO, CampaignStatus.RECHAZADO]
NO_EDITABLES = [
    CampaignStatus.PENDIENTE_IA,
    CampaignStatus.PENDIENTE_APROBACION,
    CampaignStatus.APROBADO,
    CampaignStatus.FRACASO,
]


def _url(campaign):
    return f"/api/campaigns/{campaign.pk}/"


def _con_estado(campaign, estado):
    Campaign.objects.filter(pk=campaign.pk).update(estado=estado)
    campaign.refresh_from_db()
    return campaign


class TestPatchConVersion:
    def test_la_respuesta_incluye_la_version_de_solo_lectura(self, api_client, campaign_generada):
        response = api_client.get(_url(campaign_generada))
        assert response.data["data"]["campaign"]["version"] == campaign_generada.version

    def test_guardar_con_la_version_leida_sube_una_sola_vez(self, api_client, campaign_generada):
        version = campaign_generada.version
        response = api_client.patch(
            _url(campaign_generada), {"texto_generado": "Copy nuevo", "version": version}, format="json"
        )
        assert response.status_code == 200
        assert response.data["data"]["campaign"]["version"] == version + 1
        campaign_generada.refresh_from_db()
        assert campaign_generada.version == version + 1
        assert campaign_generada.texto_generado == "Copy nuevo"

    @pytest.mark.parametrize("body", [{}, {"version": None}, {"version": "1"}, {"version": True}, {"version": 1.0}])
    def test_sin_version_entera_400(self, api_client, campaign_generada, body):
        response = api_client.patch(_url(campaign_generada), {"texto_generado": "Copy nuevo", **body}, format="json")
        assert response.status_code == 400
        assert "version" in response.data["data"]["errors"]
        campaign_generada.refresh_from_db()
        assert campaign_generada.texto_generado == "Copy generado de prueba."

    def test_version_desactualizada_409_sin_pisar(self, api_client, campaign_generada):
        version = campaign_generada.version
        primera = api_client.patch(
            _url(campaign_generada), {"texto_generado": "Desde la pestaña A", "version": version}, format="json"
        )
        segunda = api_client.patch(
            _url(campaign_generada), {"texto_generado": "Desde la pestaña B", "version": version}, format="json"
        )
        assert primera.status_code == 200
        assert segunda.status_code == 409
        assert segunda.data["data"]["version_actual"] == version + 1
        campaign_generada.refresh_from_db()
        assert campaign_generada.texto_generado == "Desde la pestaña A"
        assert campaign_generada.version == version + 1

    def test_la_version_del_body_no_se_escribe(self, api_client, campaign_generada):
        version = campaign_generada.version
        api_client.patch(_url(campaign_generada), {"prompt": "Prompt nuevo de prueba", "version": version}, format="json")
        campaign_generada.refresh_from_db()
        assert campaign_generada.version == version + 1

    @pytest.mark.parametrize("estado", EDITABLES)
    def test_estados_editables_200(self, api_client, campaign_generada, estado):
        campaign = _con_estado(campaign_generada, estado)
        response = api_client.patch(
            _url(campaign), {"texto_generado": "Editado", "version": campaign.version}, format="json"
        )
        assert response.status_code == 200

    @pytest.mark.parametrize("estado", NO_EDITABLES)
    def test_estados_no_editables_409(self, api_client, campaign_generada, estado):
        campaign = _con_estado(campaign_generada, estado)
        response = api_client.patch(
            _url(campaign), {"texto_generado": "Editado", "version": campaign.version}, format="json"
        )
        assert response.status_code == 409
        assert response.data["data"]["estado"] == estado
        campaign.refresh_from_db()
        assert campaign.texto_generado == "Copy generado de prueba."
        assert campaign.version == 1

    def test_campana_ajena_404(self, api_client, campaign_generada, superadmin):
        otra = Campaign.objects.create(
            titulo="Ajena", cliente_nombre="X", industria="retail", prompt="Prompt de otra persona",
            estado=CampaignStatus.GENERADO, marketero=superadmin,
        )
        assert api_client.patch(_url(otra), {"texto_generado": "x", "version": 1}, format="json").status_code == 404


class TestImproveTextBloqueado:
    def _mejorar(self, client, campaign, **body):
        return client.post(f"/api/campaigns/{campaign.pk}/improve-text/", body, format="json")

    @pytest.mark.parametrize("estado", NO_EDITABLES)
    def test_no_mejora_fuera_de_estados_editables(self, api_client, campaign_generada, estado):
        campaign = _con_estado(campaign_generada, estado)
        with patch("apps.campaigns.views.improve_copy") as improve:
            assert self._mejorar(api_client, campaign).status_code == 409
        improve.assert_not_called()

    def test_mejora_en_rechazado_y_sube_una_vez(self, api_client, campaign_generada):
        campaign = _con_estado(campaign_generada, CampaignStatus.RECHAZADO)
        with patch("apps.campaigns.views.improve_copy", return_value="Copy mejorado"):
            response = self._mejorar(api_client, campaign)
        assert response.status_code == 200
        campaign.refresh_from_db()
        assert campaign.texto_generado == "Copy mejorado"
        assert campaign.version == 2
        assert CampaignVersion.objects.filter(campaign=campaign).count() == 1

    def test_version_enviada_desactualizada_no_llama_a_gemini(self, api_client, campaign_generada):
        with patch("apps.campaigns.views.improve_copy") as improve:
            assert self._mejorar(api_client, campaign_generada, version=99).status_code == 409
        improve.assert_not_called()

    def test_si_la_campana_cambia_durante_gemini_no_se_guarda(self, api_client, campaign_generada):
        def editar_mientras_tanto(**kwargs):
            Campaign.objects.filter(pk=campaign_generada.pk).update(
                texto_generado="Edición concurrente", version=5
            )
            return "Copy mejorado"

        with patch("apps.campaigns.views.improve_copy", side_effect=editar_mientras_tanto):
            response = self._mejorar(api_client, campaign_generada)

        assert response.status_code == 409
        assert response.data["data"]["version_actual"] == 5
        campaign_generada.refresh_from_db()
        assert campaign_generada.texto_generado == "Edición concurrente"
        assert campaign_generada.version == 5
        assert not CampaignVersion.objects.filter(campaign=campaign_generada).exists()
