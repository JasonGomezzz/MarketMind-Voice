"""
MarketMind Voice — Programar y publicar campañas aprobadas en Meta.

Flujo:
1. Al enviar al cliente, el marketero elige destinos → Publication en
   'esperando_aprobacion' (programar_publicaciones).
2. Cuando el cliente aprueba en Spring, Spring avisa a Django tras su commit
   → publicar_campana_aprobada congela copy + imagen y publica.
3. Si algo falla, el marketero puede reintentar (reintentar_publicacion).

Garantías (verificadas con tests, no con Meta real):
- Una publicación se reclama con bloqueo de fila: dos avisos simultáneos no
  publican dos veces.
- Se publica el contenido congelado al aprobar, no el actual de la campaña.
- Un fallo ambiguo de Instagram no se reintenta a ciegas: primero se consulta
  si el contenedor ya quedó publicado.
- La llamada a Meta ocurre fuera de la transacción.
"""

import logging
from dataclasses import dataclass

from django.db import transaction
from django.db.models import Q
from django.utils import timezone

from apps.authentication.models import User, UserRole
from apps.campaigns.models import Campaign, CampaignStatus
from apps.social.models import (
    ConexionEstado,
    PublicacionEstado,
    Publication,
    RedSocial,
    SocialConnection,
)
from services import meta_graph, public_media
from services.social_tokens import TokenIlegible, descifrar

logger = logging.getLogger(__name__)

MAX_INTENTOS = 3


class DestinoInvalido(Exception):
    pass


class PublicacionNoPermitida(Exception):
    pass


def conexiones_disponibles(marketero: User, cliente_email: str | None) -> list[SocialConnection]:
    """Cuentas activas donde el marketero puede publicar: las del cliente y las suyas."""
    filtro = Q(usuario=marketero)
    if cliente_email:
        filtro |= Q(usuario__email__iexact=cliente_email, usuario__rol=UserRole.CLIENTE)
    return list(
        SocialConnection.objects.filter(filtro, estado=ConexionEstado.ACTIVA).select_related("usuario")
    )


def programar_publicaciones(campaign: Campaign, conexion_ids: list[int], marketero: User) -> list[Publication]:
    """Crea (o reutiliza) una Publication por destino elegido. Llamar dentro de la transacción de submit."""
    if not conexion_ids:
        return []
    permitidas = {c.id: c for c in conexiones_disponibles(marketero, campaign.cliente_email)}
    desconocidas = [cid for cid in conexion_ids if cid not in permitidas]
    if desconocidas:
        raise DestinoInvalido(
            "Alguna cuenta destino no existe, está desconectada o no pertenece al cliente ni al marketero."
        )
    publicaciones = []
    for cid in dict.fromkeys(conexion_ids):
        conexion = permitidas[cid]
        publicacion, _ = Publication.objects.get_or_create(
            campaign=campaign,
            conexion=conexion,
            defaults={
                "red": conexion.red,
                "cuenta_nombre": conexion.cuenta_nombre,
                "solicitada_por": marketero,
            },
        )
        publicaciones.append(publicacion)
    return publicaciones


@dataclass
class ResumenPublicacion:
    publicadas: int = 0
    fallidas: int = 0
    omitidas: int = 0


def publicar_campana_aprobada(campaign_id: int) -> ResumenPublicacion:
    """Publica todas las publicaciones pendientes de una campaña aprobada. Idempotente."""
    resumen = ResumenPublicacion()
    ids = list(
        Publication.objects.filter(
            campaign_id=campaign_id, estado=PublicacionEstado.ESPERANDO_APROBACION
        ).values_list("id", flat=True)
    )
    for publication_id in ids:
        resultado = _publicar(publication_id, desde=(PublicacionEstado.ESPERANDO_APROBACION,))
        setattr(resumen, resultado, getattr(resumen, resultado) + 1)
    return resumen


def reintentar_publicacion(publication: Publication, usuario: User) -> Publication:
    """'Publicar ahora / Reintentar' del marketero dueño de la campaña."""
    if publication.campaign.marketero_id != usuario.id:
        raise PublicacionNoPermitida("Solo el marketero de la campaña puede publicarla.")
    if publication.campaign.estado != CampaignStatus.APROBADO:
        raise PublicacionNoPermitida("La campaña todavía no fue aprobada por el cliente.")
    if publication.estado not in (PublicacionEstado.FALLIDO, PublicacionEstado.ESPERANDO_APROBACION):
        raise PublicacionNoPermitida(f"La publicación está '{publication.estado}' y no se puede reintentar.")
    if publication.intentos >= MAX_INTENTOS:
        raise PublicacionNoPermitida("Se alcanzó el máximo de intentos. Revisa la cuenta conectada.")
    _publicar(publication.id, desde=(PublicacionEstado.FALLIDO, PublicacionEstado.ESPERANDO_APROBACION))
    publication.refresh_from_db()
    return publication


def _publicar(publication_id: int, desde: tuple[str, ...]) -> str:
    """Reclama la publicación con bloqueo, publica fuera de la transacción y guarda el resultado."""
    with transaction.atomic():
        publicacion = (
            Publication.objects.select_for_update()
            .select_related("campaign", "conexion")
            .filter(pk=publication_id)
            .first()
        )
        if publicacion is None or publicacion.estado not in desde:
            return "omitidas"
        campaign = publicacion.campaign
        if campaign.estado != CampaignStatus.APROBADO:
            return "omitidas"

        # Congelar lo aprobado solo la primera vez: un reintento publica lo mismo.
        if publicacion.version_aprobada is None:
            publicacion.copy_aprobado = campaign.texto_generado
            publicacion.imagen_aprobada_b64 = campaign.imagen_b64
            publicacion.version_aprobada = campaign.version
        publicacion.estado = PublicacionEstado.PUBLICANDO
        publicacion.intentos += 1
        publicacion.error = ""
        publicacion.save()

    conexion = publicacion.conexion
    try:
        if conexion is None or conexion.estado != ConexionEstado.ACTIVA:
            raise meta_graph.MetaError("La cuenta destino fue desconectada. Vuelve a conectarla.")
        token = descifrar(conexion.token_cifrado)
        resultado = _enviar_a_meta(publicacion, conexion, token)
    except (meta_graph.MetaError, TokenIlegible) as exc:
        _marcar_fallida(publicacion, exc)
        return "fallidas"

    Publication.objects.filter(pk=publicacion.pk).update(
        estado=PublicacionEstado.PUBLICADO,
        externo_id=resultado.externo_id,
        permalink=resultado.permalink,
        contenedor_id=resultado.contenedor_id or publicacion.contenedor_id,
        publicado_at=timezone.now(),
        fecha_actualizacion=timezone.now(),
    )
    logger.info("Publicación %s publicada en %s (%s)", publicacion.pk, publicacion.red, resultado.externo_id)
    return "publicadas"


def _enviar_a_meta(publicacion: Publication, conexion: SocialConnection, token: str):
    if publicacion.red == RedSocial.INSTAGRAM:
        # Un intento anterior pudo haber publicado aunque la respuesta se perdió.
        if publicacion.contenedor_id and meta_graph.contenedor_publicado(publicacion.contenedor_id, token):
            return meta_graph.ResultadoPublicacion(
                externo_id=publicacion.externo_id, permalink=publicacion.permalink,
                contenedor_id=publicacion.contenedor_id,
            )
        imagen_url = public_media.url_publica(publicacion.pk)
        return meta_graph.publicar_instagram(conexion.cuenta_id, token, imagen_url, publicacion.copy_aprobado)
    imagen_url = public_media.url_publica(publicacion.pk)
    return meta_graph.publicar_facebook(conexion.pagina_id, token, imagen_url, publicacion.copy_aprobado)


def _marcar_fallida(publicacion: Publication, exc: Exception) -> None:
    mensaje = str(exc)
    if isinstance(exc, meta_graph.MetaError) and exc.ambiguo:
        mensaje += " El resultado es incierto: revisa la cuenta antes de reintentar."
    if isinstance(exc, meta_graph.MetaError) and exc.token_invalido and publicacion.conexion_id:
        SocialConnection.objects.filter(pk=publicacion.conexion_id).update(estado=ConexionEstado.DESCONECTADA)
        mensaje += " La cuenta quedó desconectada: el dueño debe volver a autorizarla."
    cambios = {"estado": PublicacionEstado.FALLIDO, "error": mensaje[:1000], "fecha_actualizacion": timezone.now()}
    if getattr(exc, "contenedor_id", ""):
        cambios["contenedor_id"] = exc.contenedor_id
    Publication.objects.filter(pk=publicacion.pk).update(**cambios)
    logger.warning("Publicación %s falló: %s", publicacion.pk, mensaje)
