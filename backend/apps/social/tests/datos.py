"""Datos de prueba compartidos por los tests de publicación (la fixture `campana` está en conftest.py)."""

from rest_framework.test import APIClient

from apps.authentication.models import User
from apps.campaigns.models import Campaign
from apps.social.models import Publication, RedSocial, SocialConnection
from services.mock_assets import MOCK_IMAGE_B64
from services.social_tokens import cifrar


def cliente_api(user: User) -> APIClient:
    client = APIClient()
    client.force_authenticate(user=user)
    return client


def conexion(usuario: User, red: str = RedSocial.INSTAGRAM, cuenta_id: str = "ig-1", **extra) -> SocialConnection:
    return SocialConnection.objects.create(
        usuario=usuario, red=red, cuenta_id=cuenta_id,
        cuenta_nombre=extra.pop("cuenta_nombre", "@cafe.aurora"), pagina_id=extra.pop("pagina_id", "page-1"),
        token_cifrado=cifrar("token-de-pagina"), **extra,
    )


def publicacion(campana: Campaign, con: SocialConnection, **extra) -> Publication:
    datos = {
        "campaign": campana, "conexion": con, "red": con.red, "cuenta_id": con.cuenta_id,
        "cuenta_nombre": con.cuenta_nombre, "copy_aprobado": "Copy aprobado", "version_aprobada": campana.version,
        "imagen_aprobada_b64": MOCK_IMAGE_B64, **extra,
    }
    return Publication.objects.create(**datos)
