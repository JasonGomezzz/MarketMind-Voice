"""
Publication.publicando_desde: inicio del último intento de publicar.

Las filas que ya estaban atascadas en 'publicando' toman su última
modificación, para que puedan reintentarse pasado el margen.
"""

from django.db import migrations, models
from django.db.models import F


def marcar_atascadas(apps, schema_editor):
    Publication = apps.get_model("social", "Publication")
    Publication.objects.filter(estado="publicando", publicando_desde__isnull=True).update(
        publicando_desde=F("fecha_actualizacion")
    )


class Migration(migrations.Migration):

    dependencies = [
        ("social", "0005_rellenar_cuenta_publicacion"),
    ]

    operations = [
        migrations.AddField(
            model_name="publication",
            name="publicando_desde",
            field=models.DateTimeField(blank=True, help_text="Inicio del último intento. Si el proceso murió, pasado un margen se puede reintentar.", null=True),
        ),
        migrations.RunPython(marcar_atascadas, migrations.RunPython.noop),
    ]
