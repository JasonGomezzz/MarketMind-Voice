"""
MarketMind IA — Campaign Signals
Invalida la caché de stats del marketero cuando su campaña cambia de estado.
Dispara el email al cliente (HU16) cuando la campaña transita a PENDIENTE_APROBACION.
"""

import logging

from django.core.cache import cache
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver

from .models import Campaign, CampaignStatus

logger = logging.getLogger(__name__)


@receiver(pre_save, sender=Campaign)
def cache_estado_anterior(
    sender: type, instance: Campaign, **kwargs: object
) -> None:
    """Guarda el estado anterior en el instance para que post_save detecte transición (HU16)."""
    if instance.pk:
        try:
            instance._estado_anterior = (
                Campaign.objects.only("estado").get(pk=instance.pk).estado
            )
        except Campaign.DoesNotExist:
            instance._estado_anterior = None
    else:
        instance._estado_anterior = None


@receiver(post_save, sender=Campaign)
def invalidate_stats_cache(
    sender: type, instance: Campaign, **kwargs: object
) -> None:
    """Elimina la caché de stats al guardar cualquier campaña."""
    cache.delete(f"campaign_stats_{instance.marketero_id}")


@receiver(post_save, sender=Campaign)
def disparar_email_cliente_hu16(
    sender: type, instance: Campaign, created: bool, **kwargs: object
) -> None:
    """
    HU16: dispara webhook n8n para notificar al cliente cuando la campaña
    transita a PENDIENTE_APROBACION. Idempotente: solo dispara en la transición
    real (estado anterior != estado actual) y si email_enviado=False.
    """
    if created:
        return
    anterior = getattr(instance, "_estado_anterior", None)
    if anterior == instance.estado:
        return
    if instance.estado != CampaignStatus.PENDIENTE_APROBACION:
        return
    if instance.email_enviado:
        return

    # Import diferido para evitar ciclos durante la inicialización de Django.
    from services import email_n8n_service

    try:
        email_n8n_service.disparar_email_cliente(instance)
    except Exception as exc:  # noqa: BLE001 — fire-and-forget, no romper transición
        logger.error("HU16 signal falló para campaña %s: %s", instance.pk, exc)
