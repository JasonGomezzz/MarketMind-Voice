"""
MarketMind IA — Django Production Settings
Extiende base.py con configuraciones para Render.com.
Uso: DJANGO_SETTINGS_MODULE=core.settings.prod
"""

from .base import *  # noqa: F401, F403

# ─────────────────────────────────────────────
# SECURITY
# ─────────────────────────────────────────────
DEBUG = False

STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

SECURE_HSTS_SECONDS = 31536000           # 1 año — HTTPS obligatorio
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_SSL_REDIRECT = True               # HTTP → HTTPS automático
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = "DENY"

# ─────────────────────────────────────────────
# LOGGING — errores a archivo en producción
# ─────────────────────────────────────────────
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "json": {
            "format": '{"level": "%(levelname)s", "time": "%(asctime)s", "module": "%(module)s", "message": "%(message)s"}',
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "json",
        },
    },
    "loggers": {
        "django": {"handlers": ["console"], "level": "WARNING"},
        "apps": {"handlers": ["console"], "level": "WARNING", "propagate": False},
        "services": {"handlers": ["console"], "level": "WARNING", "propagate": False},
    },
}
