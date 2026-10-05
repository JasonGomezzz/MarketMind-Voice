"""Atomic cache limits; never store email addresses or IPs in cache keys.

Hourly quotas use fixed UTC-hour buckets. Redis must be shared by workers.
These limits complement, rather than replace, gateway abuse protection.
"""
import logging
import math
import time

from django.conf import settings
from django.core.cache import cache
from django.utils.crypto import salted_hmac
from rest_framework.exceptions import APIException
from rest_framework.throttling import BaseThrottle

logger = logging.getLogger(__name__)


class RecoveryUnavailable(APIException):
    status_code = 503
    default_detail = 'La recuperación no está disponible temporalmente. Intenta más tarde.'
    default_code = 'recovery_unavailable'


def recovery_key(scope, identity):
    digest = salted_hmac('password-recovery', identity, algorithm='sha256').hexdigest()
    return f'recovery:v2:{scope}:{digest}'


class RecoveryRequestThrottle(BaseThrottle):
    scope = 'request'

    def wait(self):
        return self.retry_after

    def hourly_limit(self, scope, identity, limit, now):
        bucket = int(now // 3600)
        self.retry_after = max(1, math.ceil((bucket + 1) * 3600 - now))
        key = f'{recovery_key(scope, identity)}:{bucket}'
        if cache.add(key, 1, timeout=self.retry_after + 1):
            return True
        try:
            return cache.incr(key) <= limit
        except ValueError:
            # A concurrent cache eviction must not allow an uncounted send.
            return cache.add(key, 1, timeout=self.retry_after + 1)

    def allow_request(self, request, view):
        self.retry_after = 60
        if request.method != 'POST':
            return True
        try:
            now = time.time()
            # Do not trust arbitrary X-Forwarded-For headers. Configure the
            # ingress/server to supply a trusted REMOTE_ADDR in production.
            ip = request.META.get('REMOTE_ADDR') or 'unknown'
            if not self.hourly_limit(f'{self.scope}:ip', ip, settings.RECOVERY_IP_HOURLY_LIMIT, now):
                return False
            if self.scope != 'request':
                return True
            # Same policy for known, unknown and inactive accounts; no DB lookup.
            raw_email = request.data.get('email', '') if isinstance(request.data, dict) else ''
            if not isinstance(raw_email, str):
                return True  # Serializer will reject malformed data.
            email = raw_email.strip().lower()
            if not email or len(email) > 254:
                return True
            bucket = int(now // 3600)
            used = cache.get(f'{recovery_key("email:hour", email)}:{bucket}', 0)
            if used >= settings.RECOVERY_EMAIL_HOURLY_LIMIT:
                self.retry_after = max(1, math.ceil((bucket + 1) * 3600 - now))
                return False
            cooldown = settings.RECOVERY_EMAIL_COOLDOWN_SECONDS
            key = recovery_key('email:cooldown', email)
            if not cache.add(key, now + cooldown, timeout=cooldown):
                until = cache.get(key)
                self.retry_after = max(1, math.ceil(until - now)) if until else 1
                return False
            return self.hourly_limit('email:hour', email, settings.RECOVERY_EMAIL_HOURLY_LIMIT, now)
        except APIException:
            raise
        except Exception:
            logger.error('No se pudo comprobar el límite de recuperación; revisa la conexión con la caché.')
            raise RecoveryUnavailable() from None


class RecoveryConfirmThrottle(RecoveryRequestThrottle):
    # Independent quota: sending a link must not block using it.
    scope = 'confirm'
