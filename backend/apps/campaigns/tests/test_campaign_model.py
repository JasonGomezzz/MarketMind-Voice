"""Tests del modelo Campaign — FSM, transition_to, campos."""

import pytest
from django.core.exceptions import ValidationError

from apps.campaigns.models import Campaign, CampaignPlataforma, CampaignStatus, CampaignTono


@pytest.mark.django_db
class TestCampaignFSM:
    """Verifica todas las transiciones válidas e inválidas del FSM."""

    def test_borrador_to_pendiente_ia(self, campaign):
        campaign.transition_to(CampaignStatus.PENDIENTE_IA)
        campaign.refresh_from_db()
        assert campaign.estado == CampaignStatus.PENDIENTE_IA

    def test_pendiente_ia_to_generado(self, campaign_pendiente_ia):
        campaign_pendiente_ia.transition_to(CampaignStatus.GENERADO)
        campaign_pendiente_ia.refresh_from_db()
        assert campaign_pendiente_ia.estado == CampaignStatus.GENERADO

    def test_pendiente_ia_to_borrador(self, campaign_pendiente_ia):
        campaign_pendiente_ia.transition_to(CampaignStatus.BORRADOR)
        campaign_pendiente_ia.refresh_from_db()
        assert campaign_pendiente_ia.estado == CampaignStatus.BORRADOR

    def test_generado_to_pendiente_aprobacion(self, campaign_generada):
        campaign_generada.transition_to(CampaignStatus.PENDIENTE_APROBACION)
        campaign_generada.refresh_from_db()
        assert campaign_generada.estado == CampaignStatus.PENDIENTE_APROBACION

    def test_pendiente_aprobacion_to_aprobado(self, db, user_marketero):
        campaign = Campaign.objects.create(
            titulo="Pend Aprob",
            cliente_nombre="C",
            industria="tech",
            tono=CampaignTono.PROFESIONAL,
            plataforma=CampaignPlataforma.INSTAGRAM,
            prompt="x",
            estado=CampaignStatus.PENDIENTE_APROBACION,
            marketero=user_marketero,
        )
        campaign.transition_to(CampaignStatus.APROBADO)
        campaign.refresh_from_db()
        assert campaign.estado == CampaignStatus.APROBADO

    def test_pendiente_aprobacion_to_rechazado(self, db, user_marketero):
        campaign = Campaign.objects.create(
            titulo="Pend Rechaz",
            cliente_nombre="C",
            industria="tech",
            tono=CampaignTono.PROFESIONAL,
            plataforma=CampaignPlataforma.INSTAGRAM,
            prompt="x",
            estado=CampaignStatus.PENDIENTE_APROBACION,
            marketero=user_marketero,
        )
        campaign.transition_to(CampaignStatus.RECHAZADO)
        campaign.refresh_from_db()
        assert campaign.estado == CampaignStatus.RECHAZADO

    def test_rechazado_to_borrador(self, db, user_marketero):
        campaign = Campaign.objects.create(
            titulo="Rechazado",
            cliente_nombre="C",
            industria="tech",
            tono=CampaignTono.PROFESIONAL,
            plataforma=CampaignPlataforma.INSTAGRAM,
            prompt="x",
            estado=CampaignStatus.RECHAZADO,
            marketero=user_marketero,
        )
        campaign.transition_to(CampaignStatus.BORRADOR)
        campaign.refresh_from_db()
        assert campaign.estado == CampaignStatus.BORRADOR


@pytest.mark.django_db
class TestCampaignFSMInvalid:
    """Transiciones inválidas deben lanzar ValidationError."""

    def test_borrador_cannot_go_to_generado(self, campaign):
        with pytest.raises(ValidationError):
            campaign.transition_to(CampaignStatus.GENERADO)

    def test_borrador_cannot_go_to_aprobado(self, campaign):
        with pytest.raises(ValidationError):
            campaign.transition_to(CampaignStatus.APROBADO)

    def test_aprobado_is_final(self, db, user_marketero):
        campaign = Campaign.objects.create(
            titulo="Aprobado",
            cliente_nombre="C",
            industria="tech",
            tono=CampaignTono.PROFESIONAL,
            plataforma=CampaignPlataforma.INSTAGRAM,
            prompt="x",
            estado=CampaignStatus.APROBADO,
            marketero=user_marketero,
        )
        with pytest.raises(ValidationError):
            campaign.transition_to(CampaignStatus.BORRADOR)

    def test_invalid_status_string(self, campaign):
        with pytest.raises(ValidationError):
            campaign.transition_to("estado_inexistente")

    def test_generado_cannot_go_to_borrador(self, campaign_generada):
        with pytest.raises(ValidationError):
            campaign_generada.transition_to(CampaignStatus.BORRADOR)


@pytest.mark.django_db
class TestCampaignFields:
    def test_str_includes_titulo_estado(self, campaign):
        result = str(campaign)
        assert "Campaña Test" in result
        assert "borrador" in result

    def test_default_estado_is_borrador(self, db, user_marketero):
        campaign = Campaign.objects.create(
            titulo="Defaults",
            cliente_nombre="C",
            industria="tech",
            tono=CampaignTono.PROFESIONAL,
            plataforma=CampaignPlataforma.INSTAGRAM,
            prompt="x",
            marketero=user_marketero,
        )
        assert campaign.estado == CampaignStatus.BORRADOR

    def test_default_version_is_1(self, campaign):
        assert campaign.version == 1

    def test_n8n_callback_token_generated(self, campaign):
        assert campaign.n8n_callback_token is not None

    def test_intentos_generacion_default_zero(self, campaign):
        assert campaign.intentos_generacion == 0

    def test_tokens_consumidos_default_zero(self, campaign):
        assert campaign.tokens_consumidos == 0
