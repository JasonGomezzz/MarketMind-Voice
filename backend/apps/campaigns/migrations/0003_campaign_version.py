from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("campaigns", "0002_campaign_async_fields"),
    ]

    operations = [
        migrations.AddField(
            model_name="campaign",
            name="version",
            field=models.IntegerField(default=1, verbose_name="Versión"),
        ),
    ]
