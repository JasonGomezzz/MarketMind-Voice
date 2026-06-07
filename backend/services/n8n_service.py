"""
MarketMind IA — n8n Service (Orquestador Asíncrono)

Flujo producción (USE_MOCK_AI=False):
  1. Valida tokens_disponibles > 0 (defensa en profundidad).
  2. En transaction.atomic(): descuenta 1 token, incrementa intentos,
     transiciona campaña → PENDIENTE_IA.
  3. Dispara webhook a n8n con callback_token + callback_url.
     Timeout de 5s: n8n responde inmediatamente (modo "Respond Immediately").
  4. Si n8n no responde: rollback token + estado → BORRADOR.
  5. El resultado real llega por POST /api/campaigns/webhook/ia-result/.

Flujo mock (USE_MOCK_AI=True):
  Simula el callback directamente sin llamar a n8n.
  Útil para desarrollo local sin Docker n8n activo.
"""

import logging
from typing import TYPE_CHECKING, Any

import requests
from django.conf import settings
from django.db import transaction

from services.version_service import save_campaign_version

if TYPE_CHECKING:
    from apps.campaigns.models import Campaign

logger = logging.getLogger(__name__)


def trigger_ia_generation(campaign: "Campaign") -> dict[str, Any]:
    """
    Orquesta la generación asíncrona de copy IA para una campaña.

    Descuenta 1 token, transiciona a PENDIENTE_IA y dispara el webhook n8n.
    Django retorna 202 inmediatamente; el resultado llega por callback.

    Args:
        campaign: Objeto Campaign en estado BORRADOR con marketero cargado.

    Returns:
        Dict con claves:
            - dispatched (bool): True si el webhook fue aceptado por n8n.
            - mock (bool): True si se usó el flujo mock (solo si dispatched=True).
            - error (str): Descripción del error (solo si dispatched=False).
    """
    from apps.campaigns.models import CampaignStatus

    user = campaign.marketero

    if user.tokens_disponibles <= 0:
        logger.warning(
            "Campaña %s sin tokens disponibles para usuario %s",
            campaign.id,
            user.id,
        )
        return {"dispatched": False, "error": "Sin tokens disponibles."}

    if campaign.intentos_generacion >= 3:
        logger.warning(
            "Campaña %s alcanzó el máximo de intentos (%s)",
            campaign.id,
            campaign.intentos_generacion,
        )
        return {"dispatched": False, "error": "Máximo de intentos de generación alcanzado (3)."}

    # ── Descontar token + incrementar intentos + transicionar ──────────
    with transaction.atomic():
        user.tokens_disponibles -= 1
        user.save(update_fields=["tokens_disponibles"])

        campaign.intentos_generacion += 1
        campaign.tokens_consumidos += 1
        campaign.save(update_fields=["intentos_generacion", "tokens_consumidos", "fecha_actualizacion"])

        campaign.transition_to(CampaignStatus.PENDIENTE_IA)

    logger.info(
        "Campaña %s → PENDIENTE_IA. Tokens restantes: %s. Intento #%s.",
        campaign.id,
        user.tokens_disponibles,
        campaign.intentos_generacion,
    )

    # ── Flujo mock: simula callback sin n8n ────────────────────────────
    if settings.USE_MOCK_AI:
        logger.info("USE_MOCK_AI activo — simulando callback para campaña %s", campaign.id)
        mock_copy = (
            f"[MOCK] Copy publicitario para «{campaign.titulo}». "
            f"Industria: {campaign.industria} | Tono: {campaign.tono} | "
            f"Plataforma: {campaign.plataforma}. "
            "Transforma tu marca hoy con MarketMind IA."
        )
        save_campaign_version(campaign)
        campaign.texto_generado = mock_copy
        campaign.imagen_b64 = None  # mock no llama Gemini Imagen 3
        campaign.save(update_fields=["texto_generado", "imagen_b64", "fecha_actualizacion"])
        campaign.transition_to(CampaignStatus.GENERADO)
        return {"dispatched": True, "mock": True}

    # ── Flujo real: disparar webhook n8n ───────────────────────────────
    webhook_url = f"{settings.N8N_WEBHOOK_BASE_URL}/webhook/marketmind"
    callback_url = (
        f"{settings.DJANGO_BASE_URL}/api/campaigns/webhook/ia-result/"
    )

    payload = {
        "campaign_id": campaign.id,
        "prompt": campaign.prompt,
        "industria": campaign.industria,
        "tono": campaign.tono,
        "plataforma": campaign.plataforma,
        "n8n_callback_token": str(campaign.n8n_callback_token),
        "callback_url": callback_url,
        "use_mock": False,
    }

    try:
        response = requests.post(
            webhook_url,
            json=payload,
            timeout=settings.N8N_WEBHOOK_TIMEOUT,
        )
        if response.status_code not in (200, 202):
            raise requests.exceptions.RequestException(
                f"n8n respondió {response.status_code}"
            )

        logger.info(
            "Webhook n8n aceptado para campaña %s (status %s). Esperando callback.",
            campaign.id,
            response.status_code,
        )
        return {"dispatched": True, "mock": False}

    except (
        requests.exceptions.Timeout,
        requests.exceptions.ConnectionError,
        requests.exceptions.RequestException,
    ) as exc:
        error_msg = str(exc)
        logger.error(
            "Error al disparar webhook n8n para campaña %s: %s",
            campaign.id,
            error_msg,
        )
        # Rollback: devolver token + marcar error + estado → BORRADOR
        with transaction.atomic():
            user.tokens_disponibles += 1
            user.save(update_fields=["tokens_disponibles"])

            campaign.ia_error_message = f"n8n no disponible: {error_msg}"
            campaign.save(update_fields=["ia_error_message", "fecha_actualizacion"])

            campaign.transition_to(CampaignStatus.BORRADOR)

        logger.warning(
            "Campaña %s revertida a BORRADOR. Token devuelto a usuario %s.",
            campaign.id,
            user.id,
        )
        return {"dispatched": False, "error": error_msg}
