"""Tests de CampaignViewSet: create, list, retrieve, generate, submit, stats."""

import pytest
from rest_framework.test import APIClient

from apps.authentication.models import User, UserRole
from apps.campaigns.models import Campaign, CampaignPlataforma, CampaignStatus, CampaignTono

CAMPAIGNS_URL = "/api/campaigns/"
STATS_URL = "/api/campaigns/stats/"


def campaign_url(pk: int) -> str:
    return f"/api/campaigns/{pk}/"


def generate_url(pk: int) -> str:
    return f"/api/campaigns/{pk}/generate/"


def submit_url(pk: int) -> str:
    return f"/api/campaigns/{pk}/submit/"


VALID_PAYLOAD = {
    "titulo": "Nueva Campaña",
    "cliente_nombre": "ACME Corp",
    "cliente_email": "cliente@acme.com",
    "industria": "tecnologia",
    "tono": "profesional",
    "plataforma": "instagram",
    "prompt": "Crea una campaña epica para tecnologia.",
}


@pytest.mark.django_db
class TestCampaignCreate:
    def test_marketero_creates_campaign_202(self, api_client, user_marketero):
        response = api_client.post(CAMPAIGNS_URL, VALID_PAYLOAD, format="json")
        assert response.status_code == 202
        assert response.data["success"] is True

    def test_create_with_mock_ai_saves_copy(self, api_client):
        response = api_client.post(CAMPAIGNS_URL, VALID_PAYLOAD, format="json")
        assert response.status_code == 202
        campaign_data = response.data["data"]["campaign"]
        assert campaign_data["texto_generado"] != ""
        assert "[MOCK]" in campaign_data["texto_generado"]

    def test_create_decrements_tokens(self, api_client, user_marketero):
        initial_tokens = user_marketero.tokens_disponibles
        api_client.post(CAMPAIGNS_URL, VALID_PAYLOAD, format="json")
        user_marketero.refresh_from_db()
        assert user_marketero.tokens_disponibles == initial_tokens - 1

    def test_non_marketero_gets_403(self, cliente):
        client = APIClient()
        client.force_authenticate(user=cliente)
        response = client.post(CAMPAIGNS_URL, VALID_PAYLOAD, format="json")
        assert response.status_code == 403

    def test_superadmin_gets_403(self, superadmin_client):
        response = superadmin_client.post(CAMPAIGNS_URL, VALID_PAYLOAD, format="json")
        assert response.status_code == 403

    def test_no_tokens_returns_402(self, user_marketero, api_client):
        user_marketero.tokens_disponibles = 0
        user_marketero.save()
        response = api_client.post(CAMPAIGNS_URL, VALID_PAYLOAD, format="json")
        assert response.status_code == 402
        assert response.data["success"] is False

    def test_missing_required_fields_400(self, api_client):
        response = api_client.post(CAMPAIGNS_URL, {}, format="json")
        assert response.status_code == 400

    def test_unauthenticated_gets_401(self):
        client = APIClient()
        response = client.post(CAMPAIGNS_URL, VALID_PAYLOAD, format="json")
        assert response.status_code == 401


@pytest.mark.django_db
class TestCampaignList:
    def test_marketero_sees_own_campaigns(self, api_client, campaign, db, user_marketero):
        response = api_client.get(CAMPAIGNS_URL)
        assert response.status_code == 200
        ids = [c["id"] for c in response.data["results"]]
        assert campaign.id in ids

    def test_marketero_does_not_see_others(self, api_client, db):
        other_user = User.objects.create_user(
            email="other@test.com",
            password="Test1234!",
            nombre="Other",
            rol=UserRole.MARKETERO,
        )
        other_campaign = Campaign.objects.create(
            titulo="Other Campaign",
            cliente_nombre="Other",
            industria="tech",
            tono=CampaignTono.PROFESIONAL,
            plataforma=CampaignPlataforma.INSTAGRAM,
            prompt="other",
            marketero=other_user,
        )
        response = api_client.get(CAMPAIGNS_URL)
        ids = [c["id"] for c in response.data["results"]]
        assert other_campaign.id not in ids


@pytest.mark.django_db
class TestCampaignRetrieve:
    def test_get_own_campaign(self, api_client, campaign):
        response = api_client.get(campaign_url(campaign.pk))
        assert response.status_code == 200
        assert response.data["data"]["campaign"]["id"] == campaign.id

    def test_unauthenticated_gets_401(self, campaign):
        client = APIClient()
        response = client.get(campaign_url(campaign.pk))
        assert response.status_code == 401


@pytest.mark.django_db
class TestCampaignGenerate:
    def test_generate_borrador_returns_202(self, api_client, campaign):
        response = api_client.post(generate_url(campaign.pk))
        assert response.status_code == 202

    def test_generate_state_becomes_generado(self, api_client, campaign):
        api_client.post(generate_url(campaign.pk))
        campaign.refresh_from_db()
        assert campaign.estado == CampaignStatus.GENERADO

    def test_generate_wrong_state_returns_409(self, api_client, campaign_generada):
        response = api_client.post(generate_url(campaign_generada.pk))
        assert response.status_code == 409

    def test_generate_no_tokens_returns_402(self, api_client, user_marketero, campaign):
        user_marketero.tokens_disponibles = 0
        user_marketero.save()
        response = api_client.post(generate_url(campaign.pk))
        assert response.status_code == 402

    def test_generate_non_marketero_403(self, cliente, campaign):
        client = APIClient()
        client.force_authenticate(user=cliente)
        response = client.post(generate_url(campaign.pk))
        assert response.status_code == 403


@pytest.mark.django_db
class TestCampaignSubmit:
    def test_submit_generado_returns_200(self, api_client, campaign_generada):
        response = api_client.post(submit_url(campaign_generada.pk))
        assert response.status_code == 200
        campaign_generada.refresh_from_db()
        assert campaign_generada.estado == CampaignStatus.PENDIENTE_APROBACION

    def test_submit_wrong_state_returns_409(self, api_client, campaign):
        response = api_client.post(submit_url(campaign.pk))
        assert response.status_code == 409

    def test_submit_non_marketero_403(self, cliente, campaign_generada):
        client = APIClient()
        client.force_authenticate(user=cliente)
        response = client.post(submit_url(campaign_generada.pk))
        assert response.status_code == 403


@pytest.mark.django_db
class TestCampaignStats:
    def test_stats_returns_200(self, api_client):
        response = api_client.get(STATS_URL)
        assert response.status_code == 200
        assert response.data["success"] is True

    def test_stats_has_total(self, api_client, campaign, campaign_generada):
        response = api_client.get(STATS_URL)
        data = response.data["data"]
        assert "total" in data
        assert data["total"] == 2

    def test_stats_counts_by_estado(self, api_client, campaign, campaign_generada):
        response = api_client.get(STATS_URL)
        data = response.data["data"]
        assert data[CampaignStatus.BORRADOR] == 1
        assert data[CampaignStatus.GENERADO] == 1

    def test_stats_unauthenticated_401(self):
        client = APIClient()
        response = client.get(STATS_URL)
        assert response.status_code == 401


ANALYTICS_URL = "/api/admin/analytics/"


@pytest.mark.django_db
class TestAdminAnalyticsView:
    def test_superadmin_gets_analytics(self, superadmin_client):
        response = superadmin_client.get(ANALYTICS_URL)
        assert response.status_code == 200
        assert response.data["success"] is True

    def test_analytics_has_kpi(self, superadmin_client):
        response = superadmin_client.get(ANALYTICS_URL)
        data = response.data["data"]
        assert "kpi" in data
        assert "total_campanas" in data["kpi"]
        assert "tasa_aprobacion" in data["kpi"]

    def test_analytics_has_estados_globales(self, superadmin_client):
        response = superadmin_client.get(ANALYTICS_URL)
        data = response.data["data"]
        assert "estados_globales" in data

    def test_analytics_period_week(self, superadmin_client):
        response = superadmin_client.get(f"{ANALYTICS_URL}?period=week")
        assert response.status_code == 200
        assert response.data["data"]["periodo"] == "week"

    def test_marketero_gets_403(self, api_client):
        response = api_client.get(ANALYTICS_URL)
        assert response.status_code == 403

    def test_unauthenticated_gets_401(self):
        client = APIClient()
        response = client.get(ANALYTICS_URL)
        assert response.status_code == 401
