from django.apps import AppConfig


class SocialConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.social"
    verbose_name = "Redes sociales"

    def ready(self) -> None:
        # Después de configurar el logging de Django: el code/state del OAuth no llega a los logs.
        from .log_filters import instalar

        instalar()
