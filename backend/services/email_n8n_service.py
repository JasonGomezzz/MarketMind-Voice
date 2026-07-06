"""
MarketMind IA — Email n8n Service (HU16)

Dispara el webhook de email de n8n cuando una campaña pasa a PENDIENTE_APROBACION.
n8n se encarga del envío vía Resend con 3 reintentos a nivel de nodo HTTP Request.

Patrón fire-and-forget: si el webhook falla, se loguea pero NO se revierte la
transición de la campaña. El callback de n8n (POST /api/campaigns/webhook/email-sent/)
es la fuente de verdad para marcar email_enviado=True.
"""

import logging
from typing import TYPE_CHECKING

import requests
from django.conf import settings

if TYPE_CHECKING:
    from apps.campaigns.models import Campaign

logger = logging.getLogger(__name__)


def _truncate_words(text: str, n: int = 80) -> str:
    """Recorta `text` a las primeras `n` palabras, agregando elipsis si hubo corte."""
    palabras = (text or "").split()
    if len(palabras) <= n:
        return " ".join(palabras)
    return " ".join(palabras[:n]) + "…"


def disparar_email_cliente(campaign: "Campaign") -> None:
    """
    HU16: dispara POST al webhook /webhook/marketmind-email de n8n con event_type
    pendiente_aprobacion. Si la campaña no tiene cliente_email cargado, se omite
    silenciosamente (con log).

    Args:
        campaign: Campaña que acaba de transicionar a PENDIENTE_APROBACION.
    """
    if not campaign.cliente_email:
        logger.warning(
            "Campaña %s sin cliente_email; skip HU16 email cliente.", campaign.pk
        )
        return

    payload = {
        "event_type": "pendiente_aprobacion",
        "campaign_id": campaign.pk,
        "campaign_titulo": campaign.titulo,
        "cliente_email": campaign.cliente_email,
        "cliente_nombre": campaign.cliente_nombre,
        "copy_preview": _truncate_words(campaign.texto_generado, 80),
        "imagen_b64": campaign.imagen_b64 or "",
        "marketero_email": campaign.marketero.email,
        "marketero_nombre": campaign.marketero.nombre,
        "n8n_callback_token": str(campaign.n8n_callback_token),
        "callback_url": (
            f"{settings.DJANGO_BASE_URL}/api/campaigns/webhook/email-sent/"
        ),
    }

    url = f"{settings.N8N_WEBHOOK_BASE_URL}/webhook/marketmind-email"

    try:
        response = requests.post(
            url, json=payload, timeout=settings.N8N_WEBHOOK_TIMEOUT
        )
        if response.status_code not in (200, 202):
            logger.warning(
                "n8n email webhook respondió %s para campaña %s",
                response.status_code,
                campaign.pk,
            )
            return
        logger.info(
            "HU16 webhook email disparado para campaña %s (status %s).",
            campaign.pk,
            response.status_code,
        )
    except requests.RequestException as exc:
        logger.error(
            "HU16 webhook email a n8n falló para campaña %s: %s",
            campaign.pk,
            exc,
        )
