from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("campaigns", "0008_normalize_plataforma_tono"),
    ]

    operations = [
        migrations.AddField(
            model_name="campaign",
            name="enviado_cliente_at",
            field=models.DateTimeField(
                blank=True,
                help_text="Momento en que el marketero envió la campaña para aprobación.",
                null=True,
                verbose_name="Fecha de envío al cliente",
            ),
        ),
    ]
