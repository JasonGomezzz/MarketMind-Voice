# Generated for HU16 — email cliente

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("campaigns", "0004_campaign_feedback_rechazo"),
    ]

    operations = [
        migrations.AddField(
            model_name="campaign",
            name="cliente_email",
            field=models.EmailField(
                blank=True,
                help_text="Destino del email de notificación cuando la campaña está lista para aprobación (HU16).",
                max_length=254,
                null=True,
                verbose_name="Email del cliente",
            ),
        ),
        migrations.AddField(
            model_name="campaign",
            name="email_enviado",
            field=models.BooleanField(
                default=False,
                help_text="True tras confirmación del callback n8n de envío exitoso vía Resend (HU16).",
                verbose_name="Email cliente enviado",
            ),
        ),
    ]
