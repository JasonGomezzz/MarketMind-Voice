"""
Cliente mínimo de la Graph API de Meta: OAuth, cuentas y publicación.

Documentación consultada el 2026-10-05 (API v25.0) y revisada el 2026-10-16:
- Login manual: /dialog/oauth → /oauth/access_token (code) → fb_exchange_token (≈60 días).
  El canje usa exactamente el mismo redirect_uri que el diálogo.
- /me/accounts devuelve tokens de página sin vencimiento informado.
- Instagram: POST /{ig-id}/media (image_url JPEG público + caption) → espera
  status_code FINISHED → POST /{ig-id}/media_publish (devuelve el id del media).
- El contenedor (IG Container) solo expone id, status, status_code y
  copyright_check_status: si quedó PUBLISHED no dice qué media creó. Para
  recuperarlo se buscan los media recientes de la cuenta con el mismo caption
  (GET /{ig-id}/media con since); si no hay exactamente uno, no se adivina.
- Facebook: POST /{page-id}/photos con url + caption (devuelve id y post_id).
  Para comprobar un intento dudoso se lee /{page-id}/feed (requiere
  pages_read_engagement y pages_read_user_content).

Todas las llamadas pasan por _graph() para poder simularlas en tests.
"""

import logging
import time
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Callable, Iterable
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
    # Nota para el usuario cuando se publicó pero falta un dato (p. ej. el id).
    aviso: str = ""


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


def url_autorizacion(state: str, redirect_uri: str | None = None) -> str:
    params = {
        "client_id": settings.META_APP_ID,
        "redirect_uri": redirect_uri or settings.META_REDIRECT_URI,
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


def canjear_codigo(code: str, redirect_uri: str | None = None) -> str:
    """code → token de usuario de corta duración → token de larga duración."""
    corto = _graph(
        "GET",
        "oauth/access_token",
        client_id=settings.META_APP_ID,
        client_secret=settings.META_APP_SECRET,
        redirect_uri=redirect_uri or settings.META_REDIRECT_URI,
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


def crear_contenedor(ig_id: str, token_pagina: str, imagen_url: str, caption: str) -> str:
    return _graph("POST", f"{ig_id}/media", access_token=token_pagina, image_url=imagen_url, caption=caption)["id"]


def estado_contenedor(contenedor_id: str, token_pagina: str) -> str:
    """EXPIRED, ERROR, FINISHED, IN_PROGRESS o PUBLISHED (o "" si Meta no lo informa)."""
    return _graph("GET", contenedor_id, access_token=token_pagina, fields="status_code").get("status_code") or ""


def publicar_contenedor(
    ig_id: str,
    token_pagina: str,
    contenedor: str,
    esperar: Callable[[float], None] = time.sleep,
    intentos_estado: int = 15,
) -> ResultadoPublicacion:
    """Espera a que el contenedor esté listo y lo publica. Un MetaError lleva el contenedor_id."""
    try:
        for _ in range(intentos_estado):
            estado = estado_contenedor(contenedor, token_pagina)
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
    # Ya está publicado: si falla la lectura del enlace no es un fallo de publicación.
    return ResultadoPublicacion(
        externo_id=media, permalink=_enlace(media, token_pagina, "permalink"), contenedor_id=contenedor
    )


def publicar_instagram(
    ig_id: str,
    token_pagina: str,
    imagen_url: str,
    caption: str,
    esperar: Callable[[float], None] = time.sleep,
    intentos_estado: int = 15,
    al_crear_contenedor: Callable[[str], None] | None = None,
) -> ResultadoPublicacion:
    """
    Crea el contenedor y lo publica. al_crear_contenedor recibe su id antes de
    publicar, para guardarlo: si el proceso muere después, un reintento puede
    consultar ese contenedor en vez de crear otro post.
    """
    contenedor = crear_contenedor(ig_id, token_pagina, imagen_url, caption)
    if al_crear_contenedor:
        al_crear_contenedor(contenedor)
    return publicar_contenedor(ig_id, token_pagina, contenedor, esperar=esperar, intentos_estado=intentos_estado)


def publicar_facebook(pagina_id: str, token_pagina: str, imagen_url: str, caption: str) -> ResultadoPublicacion:
    data = _graph("POST", f"{pagina_id}/photos", access_token=token_pagina, url=imagen_url, caption=caption)
    post_id = data.get("post_id") or data.get("id", "")
    permalink = _enlace(post_id, token_pagina, "permalink_url") if post_id else ""
    return ResultadoPublicacion(externo_id=post_id, permalink=permalink)


def _enlace(objeto_id: str, token_pagina: str, campo: str) -> str:
    try:
        return _graph("GET", objeto_id, access_token=token_pagina, fields=campo).get(campo, "")
    except MetaError as exc:
        logger.warning("Publicado %s, pero no se pudo leer su enlace: %s", objeto_id, exc)
        return ""


# ── Comprobar si un intento dudoso ya publicó ────────────────────────────


def _fecha_meta(valor: str | None) -> datetime | None:
    """Meta devuelve fechas como 2026-10-06T03:31:00+0000."""
    try:
        return datetime.strptime(valor or "", "%Y-%m-%dT%H:%M:%S%z")
    except ValueError:
        return None


def _unico_con_texto(
    items: list[dict[str, Any]], campo_texto: str, texto: str, desde: datetime, excluir: Iterable[str], campo_fecha: str
) -> dict[str, Any] | None:
    """El único item con exactamente ese texto, creado desde `desde` y no usado por otra publicación."""
    excluir = set(excluir)
    buscado = texto.strip()
    coincidencias = [
        item for item in items
        if item.get("id") not in excluir
        and (item.get(campo_texto) or "").strip() == buscado
        and (fecha := _fecha_meta(item.get(campo_fecha))) is not None and fecha >= desde
    ]
    return coincidencias[0] if len(coincidencias) == 1 else None


def buscar_publicacion_instagram(
    ig_id: str, token_pagina: str, caption: str, desde: datetime, excluir: Iterable[str] = ()
) -> ResultadoPublicacion | None:
    """Media de la cuenta con ese caption publicado desde `desde`. None si no hay exactamente uno."""
    data = _graph(
        "GET", f"{ig_id}/media", access_token=token_pagina,
        fields="id,caption,permalink,timestamp", since=int(desde.timestamp()), limit=25,
    )
    item = _unico_con_texto(data.get("data", []), "caption", caption, desde, excluir, "timestamp")
    return ResultadoPublicacion(externo_id=item["id"], permalink=item.get("permalink", "")) if item else None


def buscar_publicacion_facebook(
    pagina_id: str, token_pagina: str, caption: str, desde: datetime, excluir: Iterable[str] = ()
) -> ResultadoPublicacion | None:
    """Post de la página con ese texto publicado desde `desde`. None si no hay exactamente uno."""
    data = _graph(
        "GET", f"{pagina_id}/feed", access_token=token_pagina,
        fields="id,message,permalink_url,created_time", since=int(desde.timestamp()), limit=25,
    )
    item = _unico_con_texto(data.get("data", []), "message", caption, desde, excluir, "created_time")
    return ResultadoPublicacion(externo_id=item["id"], permalink=item.get("permalink_url", "")) if item else None


# ── Métricas ─────────────────────────────────────────────────────────────

METRICAS_INSTAGRAM = "likes,comments,shares,saved,reach,views,total_interactions"
METRICAS_FACEBOOK = "post_media_view,post_total_media_view_unique,post_clicks"


def _valores_insights(data: dict[str, Any]) -> dict[str, Any]:
    valores = {}
    for metrica in data.get("data", []):
        lista = metrica.get("values") or []
        valor = lista[0].get("value") if lista else metrica.get("total_value", {}).get("value")
        valores[metrica.get("name")] = valor
    return valores


def metricas_instagram(media_id: str, token_pagina: str) -> dict[str, Any]:
    """Contadores básicos (inmediatos) + insights (pueden tardar o no existir aún)."""
    basico = _graph("GET", media_id, access_token=token_pagina, fields="like_count,comments_count")
    crudo: dict[str, Any] = {"basico": basico}
    try:
        insights = _valores_insights(_graph("GET", f"{media_id}/insights", access_token=token_pagina,
                                            metric=METRICAS_INSTAGRAM))
        crudo["insights"] = insights
    except MetaError as exc:
        insights = {}
        crudo["insights_error"] = str(exc)
    return {
        "me_gusta": insights.get("likes", basico.get("like_count")),
        "comentarios": insights.get("comments", basico.get("comments_count")),
        "compartidos": insights.get("shares"),
        "guardados": insights.get("saved"),
        "alcance": insights.get("reach"),
        "vistas": insights.get("views"),
        "interacciones": insights.get("total_interactions"),
        "crudo": crudo,
    }


def metricas_facebook(post_id: str, token_pagina: str) -> dict[str, Any]:
    basico = _graph(
        "GET", post_id, access_token=token_pagina,
        fields="reactions.summary(total_count).limit(0),comments.summary(total_count).limit(0),shares",
    )
    crudo: dict[str, Any] = {"basico": basico}
    try:
        insights = _valores_insights(_graph("GET", f"{post_id}/insights", access_token=token_pagina,
                                            metric=METRICAS_FACEBOOK))
        crudo["insights"] = insights
    except MetaError as exc:
        insights = {}
        crudo["insights_error"] = str(exc)
    return {
        "me_gusta": (basico.get("reactions") or {}).get("summary", {}).get("total_count"),
        "comentarios": (basico.get("comments") or {}).get("summary", {}).get("total_count"),
        # Si Meta no incluye "shares" se guarda null (sin dato), no 0.
        "compartidos": (basico.get("shares") or {}).get("count"),
        "guardados": None,
        "alcance": insights.get("post_total_media_view_unique"),
        "vistas": insights.get("post_media_view"),
        "interacciones": insights.get("post_clicks"),
        "crudo": crudo,
    }
