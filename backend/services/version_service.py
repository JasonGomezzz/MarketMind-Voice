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
    inmutable. No-op si texto_generado está vacío o si el último snapshot
    ya tiene exactamente el mismo contenido. Conserva solo las últimas
    MAX_VERSIONS (LRU).

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
        if (
            last is not None
            and last.texto_generado == campaign.texto_generado
            and (last.imagen_b64 or "") == (campaign.imagen_b64 or "")
            and last.textos_por_plataforma == campaign.textos_por_plataforma
        ):
            return

        next_number = (last.version_number + 1) if last else 1

        CampaignVersion.objects.create(
            campaign=campaign,
            version_number=next_number,
            texto_generado=campaign.texto_generado,
            textos_por_plataforma=campaign.textos_por_plataforma,
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


def restore_campaign_version(campaign: Campaign, version: CampaignVersion) -> Campaign:
    """
    Restaura el contenido (texto_generado + imagen_b64) de un snapshot a la campaña.

    Antes de sobreescribir guarda el contenido actual como nueva versión,
    de modo que restaurar nunca pierde información (el LRU-5 sigue aplicando).
    No consume créditos de IA: es una operación de solo-copia en BD.

    Args:
        campaign: Campaña destino (debe estar en estado editable).
        version: Snapshot CampaignVersion perteneciente a la misma campaña.

    Returns:
        La campaña actualizada (refrescada desde BD).
    """
    with transaction.atomic():
        save_campaign_version(campaign)
        campaign.texto_generado = version.texto_generado
        campaign.imagen_b64 = version.imagen_b64
        campaign.textos_por_plataforma = version.textos_por_plataforma
        campaign.version += 1
        campaign.save(update_fields=['texto_generado', 'textos_por_plataforma', 'imagen_b64', 'version', 'fecha_actualizacion'])
    campaign.refresh_from_db()
    return campaign
