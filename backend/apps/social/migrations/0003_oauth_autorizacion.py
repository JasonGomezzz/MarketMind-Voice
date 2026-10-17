import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("social", "0002_metricas_publicacion"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="OAuthAutorizacion",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("proveedor", models.CharField(choices=[("meta", "Meta (Facebook e Instagram)")], default="meta", max_length=20)),
                ("state_hash", models.CharField(help_text="sha256 del state; el state no se guarda.", max_length=64, unique=True)),
                ("token_version", models.IntegerField(help_text="token_version del usuario al iniciar la conexión.")),
                ("redirect_uri", models.CharField(help_text="redirect_uri enviado a Meta; el canje del código debe usar exactamente el mismo.", max_length=500)),
                ("expira_at", models.DateTimeField()),
                ("usada_at", models.DateTimeField(blank=True, help_text="Null: todavía no se canjeó.", null=True)),
                ("fecha_creacion", models.DateTimeField(auto_now_add=True)),
                ("usuario", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="autorizaciones_oauth", to=settings.AUTH_USER_MODEL)),
            ],
            options={
                "db_table": "social_oauth_autorizaciones",
                "ordering": ["-fecha_creacion"],
            },
        ),
    ]
