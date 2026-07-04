"""
Migración de datos: normaliza valores de plataforma/tono fuera de choices.

El formulario del frontend ofreció por un tiempo 'tiktok' (plataforma) y
'persuasivo' (tono), que NO están en CampaignPlataforma/CampaignTono.
Django valida choices solo en forms/serializers, no a nivel de BD, así que
esas filas quedaron guardadas con valores inválidos (confirmado en dev:
campaña con plataforma='tiktok'). Esta migración las normaliza a los
defaults del modelo. Idempotente y segura de correr en prod (Neon).
"""

from django.db import migrations

VALID_PLATAFORMAS = ["instagram", "facebook", "twitter", "linkedin", "google_ads"]
VALID_TONOS = ["profesional", "casual", "urgente", "inspiracional", "humoristico"]


def normalize_choices(apps, schema_editor):
    """Reemplaza valores fuera de choices por los defaults del modelo."""
    Campaign = apps.get_model("campaigns", "Campaign")
    Campaign.objects.exclude(plataforma__in=VALID_PLATAFORMAS).update(
        plataforma="instagram"
    )
    Campaign.objects.exclude(tono__in=VALID_TONOS).update(tono="profesional")


def noop(apps, schema_editor):
    """Sin reversa: los valores originales eran inválidos."""


class Migration(migrations.Migration):

    dependencies = [
        ("campaigns", "0007_campaign_version_history"),
    ]

    operations = [
        migrations.RunPython(normalize_choices, noop),
    ]
