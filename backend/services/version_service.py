"""
MarketMind IA — Version Service
Gestiona snapshots inmutables del contenido generado por IA antes de sobreescribir.
"""

from __future__ import annotations

from django.db import transaction

from apps.campaigns.models import Campaign, CampaignVersion

MAX_VERSIONS = 5


def save_campaign_version(campaign: Campaign) -> None:
    """
    Guarda el estado actual de texto_generado e imagen_b64 como snapshot
    inmutable antes de sobreescribir. No-op si texto_generado está vacío.
    Conserva solo las últimas MAX_VERSIONS (LRU).

    Debe llamarse ANTES de modificar campaign.texto_generado.

    Args:
        campaign: Instancia de Campaign con texto_generado actual.
    """
    if not campaign.texto_generado:
        return

    with transaction.atomic():
        last = (
            CampaignVersion.objects
            .filter(campaign=campaign)
            .order_by('-version_number')
            .first()
        )
        next_number = (last.version_number + 1) if last else 1

        CampaignVersion.objects.create(
            campaign=campaign,
            version_number=next_number,
            texto_generado=campaign.texto_generado,
            imagen_b64=campaign.imagen_b64,
        )

        ids_to_delete = list(
            CampaignVersion.objects
            .filter(campaign=campaign)
            .order_by('-version_number')
            .values_list('id', flat=True)[MAX_VERSIONS:]
        )
        if ids_to_delete:
            CampaignVersion.objects.filter(id__in=ids_to_delete).delete()
