from django.db import migrations, models


def seed_auth_brand_content(apps, schema_editor):
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


def unseed_auth_brand_content(apps, schema_editor):
    AuthBrandContent = apps.get_model("authentication", "AuthBrandContent")
    AuthBrandContent.objects.filter(screen__in=["login", "register"]).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("authentication", "0002_user_tokens_disponibles"),
    ]

    operations = [
        migrations.CreateModel(
            name="AuthBrandContent",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                (
                    "screen",
                    models.CharField(
                        choices=[("login", "Login"), ("register", "Register")],
                        max_length=20,
                        unique=True,
                        verbose_name="Pantalla",
                    ),
                ),
                ("quote", models.TextField(verbose_name="Frase testimonial")),
                ("person_name", models.CharField(max_length=120, verbose_name="Persona")),
                ("person_role", models.CharField(max_length=180, verbose_name="Cargo")),
                (
                    "person_image",
                    models.CharField(
                        default="/src/assets/landing/testimonial.png",
                        max_length=255,
                        verbose_name="Ruta de imagen",
                    ),
                ),
            ],
            options={
                "verbose_name": "Contenido de panel auth",
                "verbose_name_plural": "Contenidos de panel auth",
                "db_table": "auth_brand_content",
                "ordering": ["screen"],
            },
        ),
        migrations.RunPython(seed_auth_brand_content, unseed_auth_brand_content),
    ]
