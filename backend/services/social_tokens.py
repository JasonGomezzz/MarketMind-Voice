"""
Cifrado de tokens de Meta en reposo (Fernet: AES-128-CBC + HMAC-SHA256).

La clave sale de SOCIAL_TOKEN_KEY. En DEBUG o en tests, si falta, se deriva
de SECRET_KEY para no frenar el desarrollo; fuera de DEBUG es obligatoria y
su ausencia falla en cuanto se intenta guardar o leer un token.
"""

import base64
import hashlib

from cryptography.fernet import Fernet, InvalidToken
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured


class TokenIlegible(Exception):
    """El token no se pudo descifrar (clave cambiada o dato corrupto)."""


def _fernet() -> Fernet:
    clave = settings.SOCIAL_TOKEN_KEY
    if not clave:
        if not (settings.DEBUG or getattr(settings, "TESTING", False)):
            raise ImproperlyConfigured("Falta SOCIAL_TOKEN_KEY para cifrar los tokens de Meta.")
        clave = base64.urlsafe_b64encode(hashlib.sha256(settings.SECRET_KEY.encode()).digest()).decode()
    return Fernet(clave.encode() if isinstance(clave, str) else clave)


def cifrar(token: str) -> str:
    return _fernet().encrypt(token.encode()).decode()


def descifrar(token_cifrado: str) -> str:
    try:
        return _fernet().decrypt(token_cifrado.encode()).decode()
    except InvalidToken as exc:
        raise TokenIlegible("No se pudo leer el token de la cuenta conectada.") from exc
