"""
MarketMind IA — Test Settings
SQLite in-memory, cache local, sin throttling.
Uso: DJANGO_SETTINGS_MODULE=core.settings.test (configurado en pytest.ini)
"""

from .base import *  # noqa: F401, F403

DEBUG = False
TESTING = True

# ── DB in-memory para velocidad y aislamiento ──
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
}

# ── Cache local (no Redis) ──
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
    }
}

# ── Throttle: scopes presentes para no romper get_rate(); cache se limpia
#    entre tests con fixture clear_cache, así cada request parte de 0 ──
REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"] = {  # noqa: F405
    "register": "1000/min",
    "login": "1000/min",
    "anon": "1000/min",
    "user": "1000/min",
    "intent_interpret": "1000/min",
}

# ── Sin llamadas reales a n8n ──
USE_MOCK_AI = True
N8N_WEBHOOK_BASE_URL = "http://mock-n8n"
DJANGO_BASE_URL = "http://testserver"

# ── Password hasher más rápido en tests ──
PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.MD5PasswordHasher",
]

# ── Meta: valores ficticios; los tests simulan la Graph API ──
META_APP_ID = "test-app"
META_APP_SECRET = "test-secret"
FRONTEND_URL = "http://frontend.test"
