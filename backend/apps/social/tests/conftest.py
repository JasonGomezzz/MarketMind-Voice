"""Fixtures de los tests de redes sociales. test_social.py define su propia `campana` (en 'generado')."""

import pytest

from apps.campaigns.models import Campaign, CampaignStatus
from services.mock_assets import MOCK_IMAGE_B64


@pytest.fixture
def campana(db, user_marketero, cliente) -> Campaign:
    """Campaña ya aprobada por el cliente, lista para publicar."""
    return Campaign.objects.create(
        titulo="2x1 en capuchinos", cliente_nombre="Café Aurora", cliente_email=cliente.email,
        industria="gastronomia", tono="casual", plataforma="instagram", prompt="Campaña 2x1 para universitarios",
        estado=CampaignStatus.APROBADO, texto_generado="Copy aprobado", imagen_b64=MOCK_IMAGE_B64,
        marketero=user_marketero,
    )
