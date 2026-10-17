"""Export PDF: WeasyPrint es opcional y su ausencia responde 503, no 500."""

import builtins
from unittest.mock import MagicMock, patch

import pytest

from apps.campaigns import views
from apps.campaigns.models import Campaign, CampaignStatus

pytestmark = pytest.mark.django_db


def _url(campaign):
    return f"/api/campaigns/{campaign.pk}/export-pdf/"


@pytest.fixture
def aprobada(campaign_generada):
    Campaign.objects.filter(pk=campaign_generada.pk).update(estado=CampaignStatus.APROBADO)
    campaign_generada.refresh_from_db()
    return campaign_generada


def test_sin_weasyprint_responde_503_con_mensaje(api_client, aprobada):
    with patch.object(views, "_cargar_weasyprint", return_value=None):
        response = api_client.get(_url(aprobada))
    assert response.status_code == 503
    assert response.data["success"] is False
    assert "PDF no está disponible" in response.data["message"]


def test_con_weasyprint_devuelve_el_pdf(api_client, aprobada):
    html = MagicMock()
    html.return_value.write_pdf.return_value = b"%PDF-1.7 prueba"
    with patch.object(views, "_cargar_weasyprint", return_value=html):
        response = api_client.get(_url(aprobada))
    assert response.status_code == 200
    assert response["Content-Type"] == "application/pdf"
    assert response.content.startswith(b"%PDF")


def test_las_reglas_de_acceso_van_antes_que_weasyprint(api_client, campaign_generada):
    with patch.object(views, "_cargar_weasyprint") as cargar:
        assert api_client.get(_url(campaign_generada)).status_code == 400  # no aprobada
    cargar.assert_not_called()


@pytest.mark.parametrize("error", [ImportError("no module"), OSError("cannot load library 'libpango'")])
def test_cargar_weasyprint_devuelve_none_si_no_carga(error):
    import_real = builtins.__import__

    def import_falso(name, *args, **kwargs):
        if name == "weasyprint":
            raise error
        return import_real(name, *args, **kwargs)

    with patch("builtins.__import__", side_effect=import_falso):
        assert views._cargar_weasyprint() is None
