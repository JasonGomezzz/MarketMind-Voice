"""
MarketMind IA — n8n Service
Dispara la generación de contenido IA a través del webhook de n8n.

Si USE_MOCK_AI=True devuelve datos fijos sin llamar a n8n.
Esto evita consumir cuota de Gemini en desarrollo.
"""

import logging
from typing import Any

import requests
from django.conf import settings

logger = logging.getLogger(__name__)


def trigger_ia_generation(
    campaign_id: int,
    prompt: str,
    industria: str,
    tono: str,
    plataforma: str,
) -> dict[str, Any]:
    """
    Dispara la generación de copy e imagen IA para una campaña.

    Si USE_MOCK_AI está activo retorna datos fijos de forma inmediata.
    En caso contrario hace POST al webhook de n8n y extrae el resultado.

    Args:
        campaign_id: ID de la campaña en base de datos.
        prompt: Texto de entrada para Gemini.
        industria: Industria de la campaña (ej. 'tecnologia').
        tono: Tono del copy (ej. 'casual').
        plataforma: Plataforma objetivo (ej. 'instagram').

    Returns:
        Dict con claves:
            - success (bool): True si la generación fue exitosa.
            - copy (str): Texto publicitario generado (solo si success=True).
            - imagen_url (str): URL de imagen (solo si success=True).
            - error (str): Descripción del error (solo si success=False).
    """
    if settings.USE_MOCK_AI:
        logger.info(
            "USE_MOCK_AI activo — devolviendo mock para campaña %s", campaign_id
        )
        return {
            "success": True,
            "copy": (
                f"[MOCK] Copy publicitario para campaña {campaign_id}. "
                f"Industria: {industria}, Tono: {tono}, Plataforma: {plataforma}. "
                "Lorem ipsum dolor sit amet, consectetur adipiscing elit. "
                "Transforma tu negocio hoy."
            ),
            "imagen_url": (
                "https://via.placeholder.com/1200x628/6366f1/ffffff?text=MarketMind+IA+Mock"
            ),
        }

    webhook_url = f"{settings.N8N_WEBHOOK_BASE_URL}/webhook/marketmind"
    payload = {
        "campaign_id": campaign_id,
        "prompt": prompt,
        "industria": industria,
        "tono": tono,
        "plataforma": plataforma,
    }

    try:
        response = requests.post(webhook_url, json=payload, timeout=30)
    except requests.exceptions.Timeout:
        logger.warning("Timeout al llamar n8n para campaña %s", campaign_id)
        return {"success": False, "error": "n8n no disponible"}
    except requests.exceptions.ConnectionError:
        logger.warning("ConnectionError al llamar n8n para campaña %s", campaign_id)
        return {"success": False, "error": "n8n no disponible"}

    if response.status_code != 200:
        logger.error(
            "n8n retornó %s para campaña %s", response.status_code, campaign_id
        )
        return {"success": False, "error": f"n8n retornó {response.status_code}"}

    data = response.json()
    return {
        "success": True,
        "copy": data.get("copy", ""),
        "imagen_url": data.get("imagen_url", ""),
    }
