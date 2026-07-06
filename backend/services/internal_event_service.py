"""
Notificaciones internas Django -> Spring Boot.

Django sigue siendo dueño del ciclo de vida de campañas; Spring Boot solo
retransmite eventos al dashboard cliente mediante WebSocket.
"""

import logging

import requests
from django.conf import settings

logger = logging.getLogger(__name__)


def notify_campaign_submitted(campaign_id: int) -> None:
    """Avisa a Spring Boot que una campaña fue enviada al cliente."""
    url = f"{settings.SPRINGBOOT_INTERNAL_URL.rstrip('/')}/api/internal/campaign-events/submitted"
    try:
        response = requests.post(
            url,
            json={"campaignId": campaign_id},
            headers={"X-Internal-Event-Token": settings.INTERNAL_EVENT_TOKEN},
            timeout=2,
        )
        response.raise_for_status()
    except requests.RequestException as exc:
        logger.warning(
            "No se pudo notificar a Spring Boot sobre campaña enviada %s: %s",
            campaign_id,
            exc,
        )
