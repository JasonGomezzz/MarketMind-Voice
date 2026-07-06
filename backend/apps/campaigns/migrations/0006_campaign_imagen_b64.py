# Generated for HU21 — imagen Gemini Imagen 3

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("campaigns", "0005_campaign_email_fields"),
    ]

    operations = [
        migrations.AddField(
            model_name="campaign",
            name="imagen_b64",
            field=models.TextField(
                blank=True,
                help_text="Imagen generada por Gemini Imagen 3 en base64 (HU21). Mostrar con data:image/png;base64,<valor>.",
                null=True,
                verbose_name="Imagen base64",
            ),
        ),
    ]
