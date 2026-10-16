"""
Límites de la recuperación de contraseña, atómicos en la caché.

Portado de la rama de Piero (26d19738). Cada contador se reserva con
`cache.add` / `cache.incr`, que son atómicos en Redis y en LocMemCache, así
que peticiones simultáneas no pueden enviar más correos que el límite.

- Por IP: RECOVERY_IP_HOURLY_LIMIT solicitudes por hora (ventana fija UTC).
- Por correo: una cada RECOVERY_EMAIL_COOLDOWN_SECONDS y como máximo
  RECOVERY_EMAIL_HOURLY_LIMIT por hora, exista o no la cuenta (misma política
  para todos: el límite no revela si el correo está registrado).
- Confirmar el enlace tiene su propia cuota por IP: pedir enlaces no bloquea
  usarlos.

Las claves usan un HMAC del correo o de la IP: la caché no guarda datos
personales en claro. Si la caché falla, se responde 503 sin enviar nada
(falla cerrado). La IP sale de REMOTE_ADDR, no de X-Forwarded-For, que el
cliente puede falsificar; detrás de un proxy hay que configurar el servidor
para que REMOTE_ADDR sea la IP real.
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
    default_detail = "La recuperación no está disponible temporalmente. Intenta más tarde."
    default_code = "recovery_unavailable"


def recovery_key(scope: str, identity: str) -> str:
    digest = salted_hmac("password-recovery", identity, algorithm="sha256").hexdigest()
    return f"recovery:v1:{scope}:{digest}"


class RecoveryRequestThrottle(BaseThrottle):
    scope = "request"

    def wait(self) -> int:
        return self.retry_after

    def hourly_limit(self, scope: str, identity: str, limit: int, now: float) -> bool:
        bucket = int(now // 3600)
        self.retry_after = max(1, math.ceil((bucket + 1) * 3600 - now))
        key = f"{recovery_key(scope, identity)}:{bucket}"
        if cache.add(key, 1, timeout=self.retry_after + 1):
            return True
        try:
            return cache.incr(key) <= limit
        except ValueError:
            # La clave expiró entre add e incr: se cuenta de nuevo, nunca se deja pasar gratis.
            return bool(cache.add(key, 1, timeout=self.retry_after + 1))

    def allow_request(self, request, view) -> bool:
        self.retry_after = 60
        if request.method != "POST":
            return True
        try:
            now = time.time()
            ip = request.META.get("REMOTE_ADDR") or "unknown"
            if not self.hourly_limit(f"{self.scope}:ip", ip, settings.RECOVERY_IP_HOURLY_LIMIT, now):
                return False
            if self.scope != "request":
                return True

            # Misma política para cuentas existentes, inexistentes o inactivas: sin consultar la BD.
            raw_email = request.data.get("email", "") if hasattr(request.data, "get") else ""
            if not isinstance(raw_email, str):
                return True  # el serializer rechaza el dato mal formado
            email = raw_email.strip().lower()
            if not email or len(email) > 254:
                return True

            bucket = int(now // 3600)
            used = cache.get(f'{recovery_key("email:hour", email)}:{bucket}', 0)
            if used >= settings.RECOVERY_EMAIL_HOURLY_LIMIT:
                self.retry_after = max(1, math.ceil((bucket + 1) * 3600 - now))
                return False

            cooldown = settings.RECOVERY_EMAIL_COOLDOWN_SECONDS
            key = recovery_key("email:cooldown", email)
            if not cache.add(key, now + cooldown, timeout=cooldown):
                until = cache.get(key)
                self.retry_after = max(1, math.ceil(until - now)) if until else 1
                return False
            return self.hourly_limit("email:hour", email, settings.RECOVERY_EMAIL_HOURLY_LIMIT, now)
        except APIException:
            raise
        except Exception:
            logger.error("No se pudo comprobar el límite de recuperación; revisa la conexión con la caché.")
            raise RecoveryUnavailable() from None


class RecoveryConfirmThrottle(RecoveryRequestThrottle):
    # Cuota independiente: pedir enlaces no debe impedir usarlos.
    scope = "confirm"
