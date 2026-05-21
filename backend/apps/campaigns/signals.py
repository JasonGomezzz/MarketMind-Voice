"""
MarketMind IA — Campaign Signals
Invalida la caché de stats del marketero cuando su campaña cambia de estado.
"""

from django.core.cache import cache
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Campaign


@receiver(post_save, sender=Campaign)
def invalidate_stats_cache(
    sender: type, instance: Campaign, **kwargs: object
) -> None:
    """Elimina la caché de stats al guardar cualquier campaña."""
    cache.delete(f"campaign_stats_{instance.marketero_id}")
