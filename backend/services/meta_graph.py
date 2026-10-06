"""
Cliente mínimo de la Graph API de Meta: OAuth, cuentas y publicación.

Documentación consultada el 2026-10-05 (API v25.0):
- Login manual: /dialog/oauth → /oauth/access_token (code) → fb_exchange_token (≈60 días).
- /me/accounts devuelve tokens de página sin vencimiento informado.
- Instagram: POST /{ig-id}/media (image_url JPEG público + caption) → espera
  status_code FINISHED → POST /{ig-id}/media_publish.
- Facebook: POST /{page-id}/photos con url + caption.

Todas las llamadas pasan por _graph() para poder simularlas en tests.
"""

import logging
import time
from dataclasses import dataclass
from typing import Any, Callable
from urllib.parse import urlencode

import httpx
from django.conf import settings

logger = logging.getLogger(__name__)

TIMEOUT = 30.0
# Códigos de Graph que indican token inválido/expirado o permiso retirado.
CODIGOS_TOKEN = {190, 102, 10, 200}


class MetaError(Exception):
    def __init__(self, mensaje: str, codigo: int | None = None, ambiguo: bool = False):
        super().__init__(mensaje)
        self.codigo = codigo
        # True si la operación pudo haberse aplicado en Meta aunque falló la respuesta.
        self.ambiguo = ambiguo
        # Contenedor de Instagram ya creado cuando falló un paso posterior.
        self.contenedor_id = ""

    @property
    def token_invalido(self) -> bool:
        return self.codigo in CODIGOS_TOKEN


@dataclass
class ResultadoPublicacion:
    externo_id: str
    permalink: str
    contenedor_id: str = ""


def _base() -> str:
    return f"https://graph.facebook.com/{settings.META_GRAPH_VERSION}"


def _graph(metodo: str, ruta: str, **params: Any) -> dict[str, Any]:
    try:
        response = httpx.request(metodo, f"{_base()}/{ruta}", params=params, timeout=TIMEOUT)
    except httpx.TimeoutException as exc:
        raise MetaError("Meta no respondió a tiempo.", ambiguo=metodo == "POST") from exc
    except httpx.HTTPError as exc:
        raise MetaError("No se pudo conectar con Meta.") from exc
    try:
        data = response.json()
    except ValueError:
        data = {}
    if response.status_code >= 400 or "error" in data:
        error = data.get("error") or {}
        raise MetaError(
            error.get("message") or f"Meta respondió HTTP {response.status_code}.",
            codigo=error.get("code"),
        )
    return data


# ── OAuth ────────────────────────────────────────────────────────────────


def url_autorizacion(state: str) -> str:
    params = {
        "client_id": settings.META_APP_ID,
        "redirect_uri": settings.META_REDIRECT_URI,
        "state": state,
        "response_type": "code",
    }
    # Facebook Login for Business: los permisos los define la configuración
    # creada en la app (config_id); Meta recomienda no enviar scope con ella.
    if settings.META_LOGIN_CONFIG_ID:
        params["config_id"] = settings.META_LOGIN_CONFIG_ID
    else:
        params["scope"] = ",".join(settings.META_OAUTH_SCOPES)
    return f"https://www.facebook.com/{settings.META_GRAPH_VERSION}/dialog/oauth?{urlencode(params)}"


def canjear_codigo(code: str) -> str:
    """code → token de usuario de corta duración → token de larga duración."""
    corto = _graph(
        "GET",
        "oauth/access_token",
        client_id=settings.META_APP_ID,
        client_secret=settings.META_APP_SECRET,
        redirect_uri=settings.META_REDIRECT_URI,
        code=code,
    )["access_token"]
    return _graph(
        "GET",
        "oauth/access_token",
        grant_type="fb_exchange_token",
        client_id=settings.META_APP_ID,
        client_secret=settings.META_APP_SECRET,
        fb_exchange_token=corto,
    )["access_token"]


def paginas_con_instagram(token_usuario: str) -> list[dict[str, Any]]:
    """Páginas que el usuario administra, con su token y su Instagram vinculado si existe."""
    return _graph(
        "GET",
        "me/accounts",
        access_token=token_usuario,
        fields="id,name,access_token,instagram_business_account{id,username}",
    ).get("data", [])


# ── Publicación ──────────────────────────────────────────────────────────


def publicar_instagram(
    ig_id: str,
    token_pagina: str,
    imagen_url: str,
    caption: str,
    esperar: Callable[[float], None] = time.sleep,
    intentos_estado: int = 15,
) -> ResultadoPublicacion:
    contenedor = _graph(
        "POST", f"{ig_id}/media", access_token=token_pagina, image_url=imagen_url, caption=caption
    )["id"]
    try:
        for _ in range(intentos_estado):
            estado = _graph("GET", contenedor, access_token=token_pagina, fields="status_code").get("status_code")
            if estado == "FINISHED":
                break
            if estado in ("ERROR", "EXPIRED"):
                raise MetaError(f"Instagram no pudo procesar la imagen ({estado}).")
            esperar(2)
        else:
            raise MetaError("Instagram no terminó de procesar la imagen a tiempo; no se publicó.")

        media = _graph("POST", f"{ig_id}/media_publish", access_token=token_pagina, creation_id=contenedor)["id"]
    except MetaError as exc:
        exc.contenedor_id = contenedor
        raise
    detalle = _graph("GET", media, access_token=token_pagina, fields="permalink")
    return ResultadoPublicacion(externo_id=media, permalink=detalle.get("permalink", ""), contenedor_id=contenedor)


def contenedor_publicado(contenedor_id: str, token_pagina: str) -> bool:
    """Tras un fallo ambiguo: ¿el contenedor ya quedó publicado en Instagram?"""
    estado = _graph("GET", contenedor_id, access_token=token_pagina, fields="status_code").get("status_code")
    return estado == "PUBLISHED"


def publicar_facebook(pagina_id: str, token_pagina: str, imagen_url: str, caption: str) -> ResultadoPublicacion:
    data = _graph("POST", f"{pagina_id}/photos", access_token=token_pagina, url=imagen_url, caption=caption)
    post_id = data.get("post_id") or data.get("id", "")
    detalle = _graph("GET", post_id, access_token=token_pagina, fields="permalink_url") if post_id else {}
    return ResultadoPublicacion(externo_id=post_id, permalink=detalle.get("permalink_url", ""))
