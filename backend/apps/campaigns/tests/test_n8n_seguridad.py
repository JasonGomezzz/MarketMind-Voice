"""
Secreto compartido Django ↔ n8n (riesgo 3).

- Django envía X-NexoMark-Token al disparar los webhooks de n8n.
- Los callbacks exigen ese secreto además del n8n_callback_token.
"""

import os
import subprocess
import sys
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
import requests
from django.conf import settings
from django.test import override_settings
from rest_framework.test import APIClient

from apps.authentication.models import User
from apps.campaigns.models import Campaign, CampaignStatus
from services import email_n8n_service, n8n_service

CALLBACK_URL = "/api/campaigns/webhook/ia-result/"
EMAIL_CALLBACK_URL = "/api/campaigns/webhook/email-sent/"
BACKEND_DIR = Path(__file__).resolve().parents[3]


def saldo(user: User) -> int:
    return User.objects.values_list("tokens_disponibles", flat=True).get(pk=user.pk)


def respuesta_n8n(status_code: int) -> Mock:
    return Mock(status_code=status_code)


@pytest.fixture
def ia_real(settings):
    """Camino real hacia n8n (requests.post se simula en cada prueba)."""
    settings.USE_MOCK_AI = False


@pytest.mark.django_db
class TestCallbackExigeSecreto:
    def test_sin_cabecera_se_rechaza_sin_tocar_campana_ni_creditos(self, campaign_pendiente_ia, user_marketero):
        antes = saldo(user_marketero)
        response = APIClient().post(CALLBACK_URL, {
            "n8n_callback_token": str(campaign_pendiente_ia.n8n_callback_token),
            "success": False,
            "error": "fallo inventado para cobrar de vuelta",
        }, format="json")

        assert response.status_code == 403
        campaign_pendiente_ia.refresh_from_db()
        assert campaign_pendiente_ia.estado == CampaignStatus.PENDIENTE_IA
        assert saldo(user_marketero) == antes

    def test_cabecera_incorrecta_se_rechaza(self, campaign_pendiente_ia):
        client = APIClient()
        client.credentials(HTTP_X_NEXOMARK_TOKEN="otro-secreto")
        response = client.post(CALLBACK_URL, {
            "n8n_callback_token": str(campaign_pendiente_ia.n8n_callback_token),
            "success": True,
            "copy": "copy falso",
        }, format="json")

        assert response.status_code == 403
        campaign_pendiente_ia.refresh_from_db()
        assert campaign_pendiente_ia.texto_generado == ""

    @override_settings(N8N_WEBHOOK_TOKEN="")
    def test_secreto_vacio_nunca_autentica(self, campaign_pendiente_ia):
        client = APIClient()
        client.credentials(HTTP_X_NEXOMARK_TOKEN="")
        response = client.post(CALLBACK_URL, {
            "n8n_callback_token": str(campaign_pendiente_ia.n8n_callback_token),
            "success": True,
            "copy": "x",
        }, format="json")

        assert response.status_code == 403

    def test_secreto_correcto_y_token_no_uuid_da_403_y_no_500(self, n8n_client):
        response = n8n_client.post(CALLBACK_URL, {
            "n8n_callback_token": "no-es-un-uuid",
            "success": True,
            "copy": "x",
        }, format="json")

        assert response.status_code == 403

    def test_email_sent_sin_cabecera_se_rechaza(self, campaign_generada):
        Campaign.objects.filter(pk=campaign_generada.pk).update(estado=CampaignStatus.PENDIENTE_APROBACION)
        response = APIClient().post(EMAIL_CALLBACK_URL, {
            "n8n_callback_token": str(campaign_generada.n8n_callback_token),
            "success": True,
            "event_type": "pendiente_aprobacion",
        }, format="json")

        assert response.status_code == 403
        campaign_generada.refresh_from_db()
        assert campaign_generada.email_enviado is False


@pytest.mark.django_db
@pytest.mark.usefixtures("ia_real")
class TestDisparoAN8n:
    def test_envia_el_secreto_y_el_token_de_la_campana(self, campaign):
        with patch.object(n8n_service.requests, "post", return_value=respuesta_n8n(202)) as post:
            resultado = n8n_service.trigger_ia_generation(campaign)

        assert resultado == {"dispatched": True, "mock": False}
        kwargs = post.call_args.kwargs
        assert kwargs["headers"] == {"X-NexoMark-Token": settings.N8N_WEBHOOK_TOKEN}
        campaign.refresh_from_db()
        assert kwargs["json"]["n8n_callback_token"] == str(campaign.n8n_callback_token)
        assert campaign.estado == CampaignStatus.PENDIENTE_IA

    @pytest.mark.parametrize("status_code", [401, 403])
    def test_n8n_rechaza_el_secreto_y_se_devuelve_el_credito(self, campaign, user_marketero, status_code):
        User.objects.filter(pk=user_marketero.pk).update(tokens_disponibles=5)
        campaign.marketero.refresh_from_db()
        with patch.object(n8n_service.requests, "post", return_value=respuesta_n8n(status_code)):
            resultado = n8n_service.trigger_ia_generation(campaign)

        assert resultado["dispatched"] is False
        assert saldo(user_marketero) == 5
        campaign.refresh_from_db()
        assert campaign.estado == CampaignStatus.BORRADOR
        assert "N8N_WEBHOOK_TOKEN" in campaign.ia_error_message

    def test_n8n_no_disponible_devuelve_el_credito(self, campaign, user_marketero):
        User.objects.filter(pk=user_marketero.pk).update(tokens_disponibles=5)
        campaign.marketero.refresh_from_db()
        with patch.object(n8n_service.requests, "post", side_effect=requests.exceptions.ConnectionError("apagado")):
            resultado = n8n_service.trigger_ia_generation(campaign)

        assert resultado["dispatched"] is False
        assert saldo(user_marketero) == 5
        campaign.refresh_from_db()
        assert campaign.estado == CampaignStatus.BORRADOR

    def test_email_al_cliente_envia_el_secreto(self, campaign_generada):
        campaign_generada.cliente_email = "cliente@ejemplo.test"
        with patch.object(email_n8n_service.requests, "post", return_value=respuesta_n8n(202)) as post:
            email_n8n_service.disparar_email_cliente(campaign_generada)

        assert post.call_args.kwargs["headers"] == {"X-NexoMark-Token": settings.N8N_WEBHOOK_TOKEN}
        assert post.call_args.kwargs["json"]["n8n_callback_token"] == str(campaign_generada.n8n_callback_token)


def cargar_settings_prod(token: str) -> subprocess.CompletedProcess:
    """Importa core.settings.prod en un proceso aparte con un entorno mínimo."""
    env = {
        "PATH": os.environ.get("PATH", ""),
        "SECRET_KEY": "prueba-settings-prod-" + "x" * 40,
        "DB_NAME": "x", "DB_USER": "x", "DB_PASSWORD": "x", "DB_HOST": "127.0.0.1",
        "INTERNAL_EVENT_TOKEN": "prueba-interna-propia-0123456789",
        "N8N_WEBHOOK_TOKEN": token,
    }
    return subprocess.run(
        [sys.executable, "-c", "import core.settings.prod"],
        cwd=BACKEND_DIR, env=env, capture_output=True, text=True, timeout=60,
    )


@pytest.mark.parametrize("token", ["", "dev-n8n-webhook-token", "corto-de-menos-de-32"])
def test_produccion_exige_un_secreto_propio_y_largo(token):
    resultado = cargar_settings_prod(token)
    assert resultado.returncode != 0
    assert "N8N_WEBHOOK_TOKEN" in resultado.stderr


def test_produccion_acepta_un_secreto_propio():
    resultado = cargar_settings_prod("s" * 64)
    assert resultado.returncode == 0, resultado.stderr[-500:]
