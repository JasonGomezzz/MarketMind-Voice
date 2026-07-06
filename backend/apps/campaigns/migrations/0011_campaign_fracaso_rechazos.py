from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("campaigns", "0010_campaign_cliente_valoracion"),
    ]

    operations = [
        migrations.AddField(
            model_name="campaign",
            name="rechazos_cliente_count",
            field=models.PositiveSmallIntegerField(
                default=0,
                help_text="Cantidad acumulada de rechazos del cliente. Al segundo rechazo la campaña queda en fracaso.",
                verbose_name="Rechazos del cliente",
            ),
        ),
        migrations.AlterField(
            model_name="campaign",
            name="estado",
            field=models.CharField(
                choices=[
                    ("borrador", "Borrador"),
                    ("pendiente_ia", "Pendiente IA"),
                    ("generado", "Generado"),
                    ("pendiente_aprobacion", "Pendiente Aprobación"),
                    ("aprobado", "Aprobado"),
                    ("rechazado", "Rechazado"),
                    ("fracaso", "Fracaso"),
                ],
                db_index=True,
                default="borrador",
                max_length=30,
                verbose_name="Estado",
            ),
        ),
    ]
