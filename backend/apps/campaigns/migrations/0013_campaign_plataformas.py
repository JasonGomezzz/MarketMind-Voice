from django.db import migrations, models


def populate_plataformas(apps, schema_editor):
    Campaign = apps.get_model("campaigns", "Campaign")
    for campaign in Campaign.objects.all().only("id", "plataforma"):
        campaign.plataformas = [campaign.plataforma or "instagram"]
        campaign.save(update_fields=["plataformas"])


class Migration(migrations.Migration):
    dependencies = [
        ("campaigns", "0012_creditpurchase"),
    ]

    operations = [
        migrations.AddField(
            model_name="campaign",
            name="plataformas",
            field=models.JSONField(
                blank=True,
                default=list,
                help_text=(
                    "Lista de plataformas elegidas. El campo plataforma conserva la "
                    "primera selección para compatibilidad con clientes antiguos."
                ),
                verbose_name="Plataformas de publicación",
            ),
        ),
        migrations.RunPython(populate_plataformas, migrations.RunPython.noop),
    ]
