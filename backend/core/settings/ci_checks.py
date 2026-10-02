"""Static production configuration/model checks, without application databases.

The unit-test profile deliberately uses LocMemCache, which django-ratelimit
rejects for production. Keep production cache declarations for system checks;
use temporary SQLite only for migration-state inspection. This does not test
Redis availability, PostgreSQL constraints, or deployment readiness.
"""
from .prod import *  # noqa: F401, F403

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
}
