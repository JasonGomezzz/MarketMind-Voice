from django.db import migrations


def refresh_auth_brand_content(apps, schema_editor):
    AuthBrandContent = apps.get_model("authentication", "AuthBrandContent")
    AuthBrandContent.objects.update_or_create(
        screen="login",
        defaults={
            "quote": (
                "Revisamos propuestas con contexto, dejamos feedback claro y el equipo "
                "creativo avanza sin perseguir aprobaciones por correo."
            ),
            "person_name": "Elena Rodríguez",
            "person_role": "Directora de Marketing, Global Creative Co.",
            "person_image": "/src/assets/landing/testimonial.png",
        },
    )
    AuthBrandContent.objects.update_or_create(
        screen="register",
        defaults={
            "quote": (
                "Pasamos del brief a una campaña lista para revisar en minutos. La IA "
                "nos da velocidad sin perder control creativo."
            ),
            "person_name": "Camila Torres",
            "person_role": "Creative Lead, Prisma Studio",
            "person_image": "/src/assets/landing/testimonial.png",
        },
    )


class Migration(migrations.Migration):

    dependencies = [
        ("authentication", "0003_auth_brand_content"),
    ]

    operations = [
        migrations.RunPython(refresh_auth_brand_content, migrations.RunPython.noop),
    ]
