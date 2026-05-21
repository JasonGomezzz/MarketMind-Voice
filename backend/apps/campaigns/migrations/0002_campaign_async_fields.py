"""
Migración: campos para flujo asíncrono con n8n.
n8n_callback_token usa two-step (nullable → populate → unique)
para no violar el constraint en filas existentes.
"""

import uuid
from django.db import migrations, models


def populate_callback_tokens(apps, schema_editor):
    """Asigna un UUID único a cada campaña existente."""
    Campaign = apps.get_model("campaigns", "Campaign")
    for campaign in Campaign.objects.filter(n8n_callback_token__isnull=True):
        campaign.n8n_callback_token = uuid.uuid4()
        campaign.save(update_fields=["n8n_callback_token"])


class Migration(migrations.Migration):

    dependencies = [
        ("campaigns", "0001_initial"),
    ]

    operations = [
        # ── Campos sin restricciones de unicidad ────────────────────────
        migrations.AddField(
            model_name="campaign",
            name="ia_error_message",
            field=models.TextField(
                blank=True,
                help_text="Último error devuelto por n8n/Gemini.",
                null=True,
                verbose_name="Error IA",
            ),
        ),
        migrations.AddField(
            model_name="campaign",
            name="intentos_generacion",
            field=models.IntegerField(
                default=0,
                help_text="Máximo 3 intentos por campaña.",
                verbose_name="Intentos de generación",
            ),
        ),
        migrations.AddField(
            model_name="campaign",
            name="tokens_consumidos",
            field=models.IntegerField(default=0, verbose_name="Tokens consumidos"),
        ),
        # ── n8n_callback_token: nullable primero ────────────────────────
        migrations.AddField(
            model_name="campaign",
            name="n8n_callback_token",
            field=models.UUIDField(
                null=True,
                blank=True,
                editable=False,
                help_text="UUID para autenticar el callback de n8n. No exponer al frontend.",
                verbose_name="Token callback n8n",
            ),
        ),
        # ── Poblamos filas existentes con UUIDs únicos ──────────────────
        migrations.RunPython(populate_callback_tokens, migrations.RunPython.noop),
        # ── Ahora aplicamos unique + not null ───────────────────────────
        migrations.AlterField(
            model_name="campaign",
            name="n8n_callback_token",
            field=models.UUIDField(
                default=uuid.uuid4,
                unique=True,
                editable=False,
                help_text="UUID para autenticar el callback de n8n. No exponer al frontend.",
                verbose_name="Token callback n8n",
            ),
        ),
    ]
