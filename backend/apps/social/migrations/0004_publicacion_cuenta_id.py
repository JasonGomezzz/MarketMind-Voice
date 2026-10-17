from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("social", "0003_oauth_autorizacion"),
    ]

    operations = [
        migrations.AddField(
            model_name="publication",
            name="cuenta_id",
            field=models.CharField(blank=True, default="", help_text="ID en Meta de la cuenta destino (copia de la conexión). Si cliente y marketero conectaron la misma cuenta, la campaña se publica una sola vez en ella.", max_length=64),
        ),
        migrations.AddConstraint(
            model_name="publication",
            constraint=models.UniqueConstraint(condition=models.Q(("cuenta_id", ""), _negated=True), fields=("campaign", "red", "cuenta_id"), name="uniq_publicacion_campana_red_cuenta"),
        ),
    ]
