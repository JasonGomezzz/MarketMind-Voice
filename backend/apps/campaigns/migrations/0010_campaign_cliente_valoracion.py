from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("campaigns", "0009_campaign_enviado_cliente_at"),
    ]

    operations = [
        migrations.AddField(
            model_name="campaign",
            name="cliente_valoracion",
            field=models.PositiveSmallIntegerField(
                blank=True,
                help_text="Valoración de 1 a 5 estrellas enviada por el cliente al aprobar o rechazar.",
                null=True,
                validators=[MinValueValidator(1), MaxValueValidator(5)],
                verbose_name="Valoración del cliente",
            ),
        ),
        migrations.AddField(
            model_name="campaign",
            name="cliente_valoracion_at",
            field=models.DateTimeField(
                blank=True,
                help_text="Momento en que el cliente registró su valoración.",
                null=True,
                verbose_name="Fecha de valoración del cliente",
            ),
        ),
    ]
