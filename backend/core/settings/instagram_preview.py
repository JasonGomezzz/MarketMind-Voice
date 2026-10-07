"""Temporary local OAuth test server: no debug, admin or campaign endpoints."""
from .base import *  # noqa: F401, F403

DEBUG = False
ALLOWED_HOSTS = ['127.0.0.1', 'localhost']
ROOT_URLCONF = 'core.instagram_preview_urls'
