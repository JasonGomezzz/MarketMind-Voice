"""
MarketMind Voice — Endpoints de redes sociales.

    GET    /api/social/meta/connect/                 URL de autorización de Meta (marketero o cliente)
    GET    /api/social/meta/callback/                Meta vuelve aquí con ?code&state (sin JWT)
    GET    /api/social/connections/                  cuentas que conectó el usuario
    GET    /api/social/connections/destinos/?cliente_email=   destinos posibles al enviar (marketero)
    DELETE /api/social/connections/{id}/             desconectar
    GET    /api/social/publications/?campaign={id}   publicaciones de una campaña (marketero dueño)
    POST   /api/social/publications/{id}/publish/    publicar ahora / reintentar
    GET    /api/public/media/{token}.jpg             imagen aprobada para Meta (firmada, caduca)
    POST   /api/internal/campaign-events/approved    aviso de Spring tras aprobar (token interno)
"""

import hmac
import logging
import secrets
from urllib.parse import urlencode

from django.conf import settings
from django.core import signing
from django.db import transaction
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.authentication.models import UserRole
from core.exceptions import api_response
from services import meta_graph, public_media
from services.publication_service import (
    PublicacionNoPermitida,
    conexiones_disponibles,
    publicar_campana_aprobada,
    reintentar_publicacion,
)
from services.social_tokens import cifrar

from .models import ConexionEstado, Publication, RedSocial, SocialConnection
from .serializers import PublicationSerializer, SocialConnectionSerializer

logger = logging.getLogger(__name__)

STATE_SALT = "marketmind.meta-oauth"
STATE_MAX_AGE = 600


def _redirigir_a_ajustes(**params: str) -> HttpResponseRedirect:
    return HttpResponseRedirect(f"{settings.FRONTEND_URL.rstrip('/')}/settings?{urlencode(params)}")


class MetaConnectView(APIView):
    """Devuelve la URL del diálogo de Meta. El state firmado identifica al usuario al volver."""

    permission_classes = [IsAuthenticated]

    def get(self, request: Request) -> Response:
        if request.user.rol not in (UserRole.MARKETERO, UserRole.CLIENTE):
            return Response(
                api_response(False, "Solo marketeros y clientes conectan redes.", {}),
                status=status.HTTP_403_FORBIDDEN,
            )
        if not (settings.META_APP_ID and settings.META_APP_SECRET):
            return Response(
                api_response(False, "La conexión con Meta todavía no está configurada en el servidor.", {}),
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )
        state = signing.dumps({"u": request.user.id, "n": secrets.token_urlsafe(8)}, salt=STATE_SALT)
        return Response(api_response(True, "Redirige al usuario a Meta.", {"url": meta_graph.url_autorizacion(state)}))


class MetaCallbackView(APIView):
    """Meta redirige el navegador aquí. Sin JWT: el usuario sale del state firmado."""

    authentication_classes: list = []
    permission_classes = [AllowAny]

    def get(self, request: Request) -> HttpResponseRedirect:
        if request.query_params.get("error"):
            return _redirigir_a_ajustes(redes="cancelado")
        try:
            datos = signing.loads(request.query_params.get("state", ""), salt=STATE_SALT, max_age=STATE_MAX_AGE)
            usuario_id = int(datos["u"])
        except (signing.BadSignature, KeyError, TypeError, ValueError):
            return _redirigir_a_ajustes(redes="error", motivo="sesion")
        code = request.query_params.get("code")
        if not code:
            return _redirigir_a_ajustes(redes="error", motivo="sin_codigo")

        try:
            token_usuario = meta_graph.canjear_codigo(code)
            paginas = meta_graph.paginas_con_instagram(token_usuario)
        except meta_graph.MetaError as exc:
            logger.warning("Callback de Meta falló para usuario %s: %s", usuario_id, exc)
            return _redirigir_a_ajustes(redes="error", motivo="meta")

        conectadas = 0
        with transaction.atomic():
            for pagina in paginas:
                token = pagina.get("access_token")
                if not token:
                    continue
                token_cifrado = cifrar(token)
                conectadas += _guardar(usuario_id, RedSocial.FACEBOOK, pagina["id"], pagina.get("name", ""),
                                       pagina["id"], token_cifrado)
                instagram = pagina.get("instagram_business_account")
                if instagram:
                    conectadas += _guardar(usuario_id, RedSocial.INSTAGRAM, instagram["id"],
                                           f"@{instagram.get('username', instagram['id'])}", pagina["id"],
                                           token_cifrado)
        if not conectadas:
            return _redirigir_a_ajustes(redes="error", motivo="sin_paginas")
        return _redirigir_a_ajustes(redes="conectadas", cuentas=str(conectadas))


def _guardar(usuario_id: int, red: str, cuenta_id: str, nombre: str, pagina_id: str, token_cifrado: str) -> int:
    SocialConnection.objects.update_or_create(
        usuario_id=usuario_id,
        red=red,
        cuenta_id=cuenta_id,
        defaults={
            "cuenta_nombre": nombre[:150],
            "pagina_id": pagina_id,
            "token_cifrado": token_cifrado,
            "estado": ConexionEstado.ACTIVA,
        },
    )
    return 1


class SocialConnectionViewSet(viewsets.GenericViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = SocialConnectionSerializer

    def get_queryset(self):
        return SocialConnection.objects.filter(usuario=self.request.user).select_related("usuario")

    def list(self, request: Request) -> Response:
        conexiones = self.get_queryset().filter(estado=ConexionEstado.ACTIVA)
        return Response(api_response(True, "Cuentas conectadas.", {
            "conexiones": SocialConnectionSerializer(conexiones, many=True).data,
        }))

    def destroy(self, request: Request, pk: str | None = None) -> Response:
        conexion = get_object_or_404(self.get_queryset(), pk=pk)
        conexion.estado = ConexionEstado.DESCONECTADA
        conexion.token_cifrado = ""
        conexion.save(update_fields=["estado", "token_cifrado", "fecha_actualizacion"])
        return Response(api_response(True, "Cuenta desconectada.", {}))

    @action(detail=False, methods=["get"], url_path="destinos")
    def destinos(self, request: Request) -> Response:
        """Cuentas donde el marketero puede publicar una campaña de ese cliente."""
        if request.user.rol != UserRole.MARKETERO:
            return Response(
                api_response(False, "Solo el marketero elige destinos.", {}),
                status=status.HTTP_403_FORBIDDEN,
            )
        conexiones = conexiones_disponibles(request.user, request.query_params.get("cliente_email"))
        return Response(api_response(True, "Destinos disponibles.", {
            "conexiones": SocialConnectionSerializer(conexiones, many=True).data,
        }))


class PublicationViewSet(viewsets.GenericViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = PublicationSerializer

    def get_queryset(self):
        qs = Publication.objects.select_related("campaign")
        if self.request.user.rol == UserRole.SUPERADMIN:
            return qs
        return qs.filter(campaign__marketero=self.request.user)

    def list(self, request: Request) -> Response:
        qs = self.get_queryset()
        campaign_id = request.query_params.get("campaign")
        if campaign_id:
            qs = qs.filter(campaign_id=campaign_id)
        return Response(api_response(True, "Publicaciones.", {
            "publicaciones": PublicationSerializer(qs[:100], many=True).data,
        }))

    @action(detail=True, methods=["post"], url_path="publish")
    def publish(self, request: Request, pk: str | None = None) -> Response:
        publicacion = get_object_or_404(self.get_queryset(), pk=pk)
        try:
            publicacion = reintentar_publicacion(publicacion, request.user)
        except PublicacionNoPermitida as exc:
            return Response(api_response(False, str(exc), {}), status=status.HTTP_409_CONFLICT)
        ok = publicacion.estado == "publicado"
        return Response(
            api_response(ok, "Publicado." if ok else "No se pudo publicar.", {
                "publicacion": PublicationSerializer(publicacion).data,
            }),
            status=status.HTTP_200_OK if ok else status.HTTP_502_BAD_GATEWAY,
        )


class PublicMediaView(APIView):
    """Imagen aprobada en JPEG para que Meta la descargue. Pública, firmada y con caducidad."""

    authentication_classes: list = []
    permission_classes = [AllowAny]

    def get(self, request: Request, token: str) -> HttpResponse:
        try:
            publication_id = public_media.leer_firma(token)
        except (signing.BadSignature, ValueError):
            return HttpResponse(status=404)
        publicacion = Publication.objects.filter(pk=publication_id).only("imagen_aprobada_b64").first()
        if publicacion is None:
            return HttpResponse(status=404)
        try:
            jpeg = public_media.a_jpeg(publicacion.imagen_aprobada_b64)
        except public_media.ImagenNoDisponible:
            return HttpResponse(status=404)
        response = HttpResponse(jpeg, content_type="image/jpeg")
        response["Cache-Control"] = "private, max-age=300"
        return response


class InternalApprovedEventView(APIView):
    """Spring avisa, después de su commit, que el cliente aprobó la campaña."""

    authentication_classes: list = []
    permission_classes = [AllowAny]

    def post(self, request: Request) -> Response:
        token = request.headers.get("X-Internal-Event-Token", "")
        if not hmac.compare_digest(token.encode(), settings.INTERNAL_EVENT_TOKEN.encode()):
            return Response(api_response(False, "Token interno inválido.", {}), status=status.HTTP_403_FORBIDDEN)
        try:
            campaign_id = int(request.data.get("campaignId"))
        except (TypeError, ValueError):
            return Response(api_response(False, "campaignId inválido.", {}), status=status.HTTP_400_BAD_REQUEST)
        resumen = publicar_campana_aprobada(campaign_id)
        return Response(api_response(True, "Evento procesado.", {
            "publicadas": resumen.publicadas, "fallidas": resumen.fallidas, "omitidas": resumen.omitidas,
        }))
