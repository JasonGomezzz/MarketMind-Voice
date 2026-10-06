"""Créditos atómicos: no se gasta dos veces el último ni una devolución pisa otro cambio."""

from unittest.mock import patch

import pytest
import requests
from django.test import override_settings
from rest_framework.test import APIClient

from apps.authentication.models import User
from apps.campaigns.models import CampaignStatus
from services import n8n_service
from services.credit_service import agregar_creditos, consumir_credito

CALLBACK_URL = "/api/campaigns/webhook/ia-result/"


def saldo(user: User) -> int:
    return User.objects.values_list("tokens_disponibles", flat=True).get(pk=user.pk)


@pytest.mark.django_db
class TestServicioDeCreditos:
    def test_consume_solo_si_hay_saldo(self, user_marketero):
        User.objects.filter(pk=user_marketero.pk).update(tokens_disponibles=1)
        assert consumir_credito(user_marketero) is True
        assert consumir_credito(user_marketero) is False
        assert saldo(user_marketero) == 0
        assert user_marketero.tokens_disponibles == 0

    def test_agregar_suma_sobre_el_valor_de_la_base(self, user_marketero):
        user_marketero.tokens_disponibles = 50  # valor viejo en memoria
        User.objects.filter(pk=user_marketero.pk).update(tokens_disponibles=3)
        agregar_creditos(user_marketero, 2)
        assert saldo(user_marketero) == 5
        assert user_marketero.tokens_disponibles == 5


@pytest.mark.django_db
class TestCobroDeGeneracion:
    def test_no_cobra_si_otra_peticion_gasto_el_ultimo_credito(self, campaign, user_marketero):
        # La vista vio 1 crédito, pero otra petición lo gastó antes del cobro.
        user_marketero.tokens_disponibles = 1
        User.objects.filter(pk=user_marketero.pk).update(tokens_disponibles=0)
        campaign.marketero = user_marketero

        resultado = n8n_service.trigger_ia_generation(campaign)

        campaign.refresh_from_db()
        assert resultado["dispatched"] is False
        assert saldo(user_marketero) == 0
        assert campaign.estado == CampaignStatus.BORRADOR
        assert campaign.intentos_generacion == 0

    @override_settings(USE_MOCK_AI=False)
    def test_n8n_caido_devuelve_el_credito_sin_pisar_otros_cambios(self, campaign, user_marketero):
        User.objects.filter(pk=user_marketero.pk).update(tokens_disponibles=10)
        campaign.marketero.refresh_from_db()

        def caido(*args, **kwargs):
            # Mientras esperamos a n8n, otra petición gasta 2 créditos.
            User.objects.filter(pk=user_marketero.pk).update(tokens_disponibles=7)
            raise requests.exceptions.ConnectionError("n8n apagado")

        with patch.object(n8n_service.requests, "post", side_effect=caido):
            resultado = n8n_service.trigger_ia_generation(campaign)

        assert resultado["dispatched"] is False
        assert saldo(user_marketero) == 8  # 7 tras la otra petición + 1 devuelto


@pytest.mark.django_db
class TestDevolucionPorCallback:
    def test_fallo_de_ia_devuelve_el_credito_sobre_el_saldo_actual(self, campaign_pendiente_ia, user_marketero):
        User.objects.filter(pk=user_marketero.pk).update(tokens_disponibles=3)
        respuesta = APIClient().post(CALLBACK_URL, {
            "n8n_callback_token": str(campaign_pendiente_ia.n8n_callback_token),
            "success": False,
            "error": "Gemini no respondió",
        }, format="json")
        assert respuesta.status_code == 200
        assert saldo(user_marketero) == 4
