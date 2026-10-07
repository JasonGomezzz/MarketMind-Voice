"""Temporary local OAuth test server: no debug, admin or campaign endpoints."""
from .base import *  # noqa: F401, F403

DEBUG = False
ALLOWED_HOSTS = ['127.0.0.1', 'localhost']
ROOT_URLCONF = 'core.instagram_preview_urls'

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'filters': {'oauth_redaction': {'()': 'core.logging_filters.RedactOAuthQueryFilter'}},
    'handlers': {'console': {'class': 'logging.StreamHandler', 'filters': ['oauth_redaction']}},
    'loggers': {'django.server': {'handlers': ['console'], 'level': 'INFO', 'propagate': False}},
}
