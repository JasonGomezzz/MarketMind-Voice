"""Tests de IaResultCallbackView y EmailSentCallbackView."""

import pytest

from apps.campaigns.models import (
    Campaign,
    CampaignPlataforma,
    CampaignStatus,
    CampaignTono,
    CampaignVersion,
)

CALLBACK_URL = "/api/campaigns/webhook/ia-result/"
EMAIL_CALLBACK_URL = "/api/campaigns/webhook/email-sent/"


@pytest.mark.django_db
class TestIaResultCallbackSuccess:
    def test_success_callback_returns_200(self, campaign_pendiente_ia, n8n_client):
        client = n8n_client
        response = client.post(CALLBACK_URL, {
            "n8n_callback_token": str(campaign_pendiente_ia.n8n_callback_token),
            "success": True,
            "copy": "Copy publicitario de prueba generado por Gemini.",
        }, format="json")
        assert response.status_code == 200
        assert response.data["success"] is True

    def test_success_saves_texto_generado(self, campaign_pendiente_ia, n8n_client):
        client = n8n_client
        copy_text = "Texto generado por IA premium."
        client.post(CALLBACK_URL, {
            "n8n_callback_token": str(campaign_pendiente_ia.n8n_callback_token),
            "success": True,
            "copy": copy_text,
        }, format="json")
        campaign_pendiente_ia.refresh_from_db()
        assert campaign_pendiente_ia.texto_generado == copy_text

    def test_success_transitions_to_generado(self, campaign_pendiente_ia, n8n_client):
        client = n8n_client
        client.post(CALLBACK_URL, {
            "n8n_callback_token": str(campaign_pendiente_ia.n8n_callback_token),
            "success": True,
            "copy": "Copy test",
        }, format="json")
        campaign_pendiente_ia.refresh_from_db()
        assert campaign_pendiente_ia.estado == CampaignStatus.GENERADO

    def test_success_saves_initial_version(self, campaign_pendiente_ia, n8n_client):
        client = n8n_client
        copy_text = "Primera versión generada por IA."
        client.post(CALLBACK_URL, {
            "n8n_callback_token": str(campaign_pendiente_ia.n8n_callback_token),
            "success": True,
            "copy": copy_text,
        }, format="json")
        versions = CampaignVersion.objects.filter(campaign=campaign_pendiente_ia)
        assert versions.count() == 1
        assert versions.first().texto_generado == copy_text


@pytest.mark.django_db
class TestIaResultCallbackFailure:
    def test_failure_callback_returns_200(self, campaign_pendiente_ia, n8n_client):
        client = n8n_client
        response = client.post(CALLBACK_URL, {
            "n8n_callback_token": str(campaign_pendiente_ia.n8n_callback_token),
            "success": False,
            "error": "Gemini 429: quota exceeded",
        }, format="json")
        assert response.status_code == 200

    def test_failure_transitions_to_borrador(self, campaign_pendiente_ia, n8n_client):
        client = n8n_client
        client.post(CALLBACK_URL, {
            "n8n_callback_token": str(campaign_pendiente_ia.n8n_callback_token),
            "success": False,
            "error": "timeout",
        }, format="json")
        campaign_pendiente_ia.refresh_from_db()
        assert campaign_pendiente_ia.estado == CampaignStatus.BORRADOR

    def test_failure_returns_token_to_user(self, campaign_pendiente_ia, user_marketero, n8n_client):
        initial_tokens = user_marketero.tokens_disponibles
        client = n8n_client
        client.post(CALLBACK_URL, {
            "n8n_callback_token": str(campaign_pendiente_ia.n8n_callback_token),
            "success": False,
            "error": "timeout",
        }, format="json")
        user_marketero.refresh_from_db()
        assert user_marketero.tokens_disponibles == initial_tokens + 1

    def test_failure_saves_error_message(self, campaign_pendiente_ia, n8n_client):
        client = n8n_client
        error_msg = "Gemini API rate limit exceeded"
        client.post(CALLBACK_URL, {
            "n8n_callback_token": str(campaign_pendiente_ia.n8n_callback_token),
            "success": False,
            "error": error_msg,
        }, format="json")
        campaign_pendiente_ia.refresh_from_db()
        assert campaign_pendiente_ia.ia_error_message == error_msg


@pytest.mark.django_db
class TestIaResultCallbackVersion:
    """El resultado de la IA sube la versión una vez; un callback fuera de pendiente_ia no la toca."""

    def _callback(self, client, campaign, **body):
        return client.post(
            CALLBACK_URL, {"n8n_callback_token": str(campaign.n8n_callback_token), **body}, format="json"
        )

    def test_exito_sube_la_version_una_sola_vez(self, campaign_pendiente_ia, n8n_client):
        version = campaign_pendiente_ia.version
        assert self._callback(n8n_client, campaign_pendiente_ia, success=True, copy="Copy nuevo").status_code == 200
        campaign_pendiente_ia.refresh_from_db()
        assert campaign_pendiente_ia.version == version + 1

    def test_fallo_no_sube_la_version(self, campaign_pendiente_ia, n8n_client):
        version = campaign_pendiente_ia.version
        self._callback(n8n_client, campaign_pendiente_ia, success=False, error="timeout")
        campaign_pendiente_ia.refresh_from_db()
        assert campaign_pendiente_ia.version == version

    def test_callback_repetido_no_pisa_lo_editado_ni_la_version(self, campaign_pendiente_ia, n8n_client):
        assert self._callback(n8n_client, campaign_pendiente_ia, success=True, copy="Primer resultado").status_code == 200
        Campaign.objects.filter(pk=campaign_pendiente_ia.pk).update(texto_generado="Editado por el marketero")
        campaign_pendiente_ia.refresh_from_db()
        version = campaign_pendiente_ia.version

        repetido = self._callback(n8n_client, campaign_pendiente_ia, success=True, copy="Resultado repetido")

        assert repetido.status_code == 409
        campaign_pendiente_ia.refresh_from_db()
        assert campaign_pendiente_ia.texto_generado == "Editado por el marketero"
        assert campaign_pendiente_ia.version == version
        assert CampaignVersion.objects.filter(campaign=campaign_pendiente_ia).count() == 1

    @pytest.mark.parametrize("estado", [
        CampaignStatus.BORRADOR,
        CampaignStatus.PENDIENTE_APROBACION,
        CampaignStatus.APROBADO,
        CampaignStatus.RECHAZADO,
        CampaignStatus.FRACASO,
    ])
    def test_ignora_campanas_fuera_de_pendiente_ia(self, campaign_generada, n8n_client, estado):
        Campaign.objects.filter(pk=campaign_generada.pk).update(estado=estado)
        assert self._callback(n8n_client, campaign_generada, success=True, copy="Tarde").status_code == 409
        campaign_generada.refresh_from_db()
        assert campaign_generada.texto_generado == "Copy generado de prueba."
        assert campaign_generada.estado == estado
        assert campaign_generada.version == 1


@pytest.mark.django_db
class TestIaResultCallbackInvalidToken:
    def test_invalid_token_returns_403(self, n8n_client):
        client = n8n_client
        response = client.post(CALLBACK_URL, {
            "n8n_callback_token": "00000000-0000-0000-0000-000000000000",
            "success": True,
            "copy": "x",
        }, format="json")
        assert response.status_code == 403

    def test_missing_token_returns_403(self, n8n_client):
        client = n8n_client
        response = client.post(CALLBACK_URL, {
            "success": True,
            "copy": "x",
        }, format="json")
        assert response.status_code == 403


@pytest.mark.django_db
class TestEmailSentCallback:
    def test_email_callback_marks_email_enviado(self, db, user_marketero, n8n_client):
        campaign = Campaign.objects.create(
            titulo="Email Test",
            cliente_nombre="C",
            industria="tech",
            tono=CampaignTono.PROFESIONAL,
            plataforma=CampaignPlataforma.INSTAGRAM,
            prompt="x",
            estado=CampaignStatus.PENDIENTE_APROBACION,
            marketero=user_marketero,
        )
        client = n8n_client
        response = client.post(EMAIL_CALLBACK_URL, {
            "n8n_callback_token": str(campaign.n8n_callback_token),
            "success": True,
            "event_type": "pendiente_aprobacion",
        }, format="json")
        assert response.status_code == 200
        campaign.refresh_from_db()
        assert campaign.email_enviado is True

    def test_email_callback_no_event_type_does_not_set_flag(self, db, user_marketero, n8n_client):
        campaign = Campaign.objects.create(
            titulo="Email No Flag",
            cliente_nombre="C",
            industria="tech",
            tono=CampaignTono.PROFESIONAL,
            plataforma=CampaignPlataforma.INSTAGRAM,
            prompt="x",
            estado=CampaignStatus.PENDIENTE_APROBACION,
            marketero=user_marketero,
        )
        client = n8n_client
        client.post(EMAIL_CALLBACK_URL, {
            "n8n_callback_token": str(campaign.n8n_callback_token),
            "success": True,
        }, format="json")
        campaign.refresh_from_db()
        assert campaign.email_enviado is False

    def test_email_callback_invalid_token_403(self, n8n_client):
        client = n8n_client
        response = client.post(EMAIL_CALLBACK_URL, {
            "n8n_callback_token": "00000000-0000-0000-0000-000000000000",
            "success": True,
        }, format="json")
        assert response.status_code == 403
