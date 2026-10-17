"""
Rellena Publication.cuenta_id (copia de la conexión) en las filas existentes.

Si una campaña ya tenía dos publicaciones para la misma cuenta de Meta
(cliente y marketero la conectaron), una sola queda como titular: la
publicada, si la hay; si no, la más antigua. Las demás quedan con cuenta_id
vacío como historial y, si aún esperaban la aprobación, pasan a 'cancelado'
para no publicar dos veces.
"""

from django.db import migrations

MENSAJE_DUPLICADA = "Cancelada: la campaña ya se publica en esta misma cuenta desde otra conexión."


def rellenar(apps, schema_editor):
    Publication = apps.get_model("social", "Publication")

    grupos: dict[tuple, list] = {}
    filas = (
        Publication.objects.filter(cuenta_id="", conexion__isnull=False)
        .select_related("conexion")
        .order_by("id")
    )
    for publicacion in filas:
        clave = (publicacion.campaign_id, publicacion.red, publicacion.conexion.cuenta_id)
        grupos.setdefault(clave, []).append(publicacion)

    for (_, _, cuenta_id), publicaciones in grupos.items():
        titular = next((p for p in publicaciones if p.estado == "publicado"), publicaciones[0])
        titular.cuenta_id = cuenta_id
        titular.save(update_fields=["cuenta_id"])
        for duplicada in publicaciones:
            if duplicada.pk != titular.pk and duplicada.estado == "esperando_aprobacion":
                duplicada.estado = "cancelado"
                duplicada.error = MENSAJE_DUPLICADA
                duplicada.save(update_fields=["estado", "error"])


class Migration(migrations.Migration):

    dependencies = [
        ("social", "0004_publicacion_cuenta_id"),
    ]

    operations = [
        migrations.RunPython(rellenar, migrations.RunPython.noop),
    ]
