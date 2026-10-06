"""
URL pública, firmada y con caducidad para que Meta descargue la imagen.

Meta exige un JPEG accesible por URL durante el procesamiento. La imagen
aprobada vive congelada en la Publication (base64); aquí se firma su id y se
convierte a JPEG al servirla. El token no revela nada más que ese id y deja
de valer pasado PUBLIC_MEDIA_MAX_AGE.
"""

import base64
import binascii
import io

from django.conf import settings
from django.core import signing
from PIL import Image, UnidentifiedImageError

SALT = "marketmind.public-media"


class ImagenNoDisponible(Exception):
    pass


def firmar(publication_id: int) -> str:
    return signing.dumps(publication_id, salt=SALT, compress=True)


def leer_firma(token: str) -> int:
    """Devuelve el id de la publicación o lanza signing.BadSignature / SignatureExpired."""
    return int(signing.loads(token, salt=SALT, max_age=settings.PUBLIC_MEDIA_MAX_AGE))


def url_publica(publication_id: int) -> str:
    return f"{settings.DJANGO_BASE_URL.rstrip('/')}/api/public/media/{firmar(publication_id)}.jpg"


def a_jpeg(imagen_b64: str | None) -> bytes:
    if not imagen_b64:
        raise ImagenNoDisponible("La publicación no tiene imagen aprobada.")
    try:
        crudo = base64.b64decode(imagen_b64, validate=False)
        imagen = Image.open(io.BytesIO(crudo))
        imagen.load()
    except (binascii.Error, UnidentifiedImageError, OSError) as exc:
        raise ImagenNoDisponible("La imagen aprobada no es válida.") from exc
    if imagen.mode != "RGB":
        imagen = imagen.convert("RGB")
    salida = io.BytesIO()
    imagen.save(salida, format="JPEG", quality=90, optimize=True)
    return salida.getvalue()
