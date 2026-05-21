"""
MarketMind IA — Campaign Views
Endpoint REST para crear, listar y gestionar campañas publicitarias.
"""

from typing import Any

from django.core.exceptions import ValidationError
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response

from core.exceptions import api_response
from services.n8n_service import trigger_ia_generation

from .models import Campaign, CampaignStatus
from .serializers import CampaignEditSerializer, CampaignSerializer


class CampaignViewSet(viewsets.ModelViewSet):
    """
    ViewSet para campañas publicitarias.

    Permisos:
        - Todos los métodos requieren autenticación JWT.
        - Solo rol 'marketero' puede crear campañas y ejecutar generate_ia.
        - 'superadmin' ve todas las campañas.
        - 'cliente' no ve ninguna campaña.

    Endpoints:
        GET    /api/campaigns/        → list
        POST   /api/campaigns/        → create
        GET    /api/campaigns/{id}/   → retrieve
        PATCH  /api/campaigns/{id}/   → partial_update
        GET    /api/campaigns/stats/  → stats (acción custom)
    """

    serializer_class = CampaignSerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ["get", "post", "patch", "head", "options"]

    def get_queryset(self):
        """
        Filtra campañas según el rol del usuario autenticado.

        Returns:
            QuerySet filtrado por rol.
        """
        user = self.request.user
        if user.rol == "superadmin":
            return Campaign.objects.all()
        if user.rol == "marketero":
            return Campaign.objects.filter(marketero=user)
        return Campaign.objects.none()

    def create(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        """
        POST /api/campaigns/

        Crea una campaña y dispara la generación de contenido IA.
        Solo rol 'marketero' puede ejecutar este endpoint.

        Returns:
            HTTP 201 con campaña creada y contenido generado.
            HTTP 400 si hay errores de validación en los datos.
            HTTP 402 si el marketero no tiene tokens disponibles.
            HTTP 403 si el usuario no tiene rol 'marketero'.
            HTTP 503 si el servicio IA no está disponible.
        """
        if request.user.rol != "marketero":
            return Response(
                api_response(
                    success=False,
                    message="Solo los marketeros pueden crear campañas.",
                    data={},
                ),
                status=status.HTTP_403_FORBIDDEN,
            )

        serializer = CampaignSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                api_response(
                    success=False,
                    message="Error de validación en los datos enviados.",
                    data={"errors": serializer.errors},
                ),
                status=status.HTTP_400_BAD_REQUEST,
            )

        if request.user.tokens_disponibles <= 0:
            return Response(
                api_response(
                    success=False,
                    message=(
                        "Sin tokens disponibles. "
                        "Contacta al administrador para renovar tu plan."
                    ),
                    data={"tokens_disponibles": 0},
                ),
                status=status.HTTP_402_PAYMENT_REQUIRED,
            )

        campaign: Campaign = serializer.save(
            estado=CampaignStatus.BORRADOR,
            marketero=request.user,
        )

        resultado = trigger_ia_generation(
            campaign_id=campaign.id,
            prompt=campaign.prompt,
            industria=campaign.industria,
            tono=campaign.tono,
            plataforma=campaign.plataforma,
        )

        if resultado["success"]:
            campaign.texto_generado = resultado["copy"]
            campaign.imagen_url = resultado["imagen_url"]
            campaign.transition_to(CampaignStatus.PENDIENTE_IA)
            campaign.transition_to(CampaignStatus.GENERADO)
            campaign.save()

            request.user.tokens_disponibles -= 1
            request.user.save(update_fields=["tokens_disponibles"])

            return Response(
                api_response(
                    success=True,
                    message="Campaña creada y contenido generado exitosamente.",
                    data={"campaign": CampaignSerializer(campaign).data},
                ),
                status=status.HTTP_201_CREATED,
            )

        return Response(
            api_response(
                success=False,
                message="Campaña guardada como borrador. El servicio IA no está disponible.",
                data={
                    "campaign": CampaignSerializer(campaign).data,
                    "error": resultado.get("error", "Error desconocido"),
                },
            ),
            status=status.HTTP_503_SERVICE_UNAVAILABLE,
        )

    def retrieve(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        """GET /api/campaigns/{id}/ — devuelve campaña individual con envoltura api_response."""
        campaign = self.get_object()
        return Response(
            api_response(
                success=True,
                message="Campaña obtenida.",
                data={"campaign": CampaignSerializer(campaign).data},
            ),
            status=status.HTTP_200_OK,
        )

    def partial_update(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        """
        PATCH /api/campaigns/{id}/

        Actualiza texto_generado. Bloqueado si estado es aprobado o rechazado.
        """
        campaign = self.get_object()

        if campaign.estado in [CampaignStatus.APROBADO, CampaignStatus.RECHAZADO]:
            return Response(
                api_response(
                    success=False,
                    message=f"No se puede editar una campaña en estado '{campaign.estado}'.",
                    data={},
                ),
                status=status.HTTP_409_CONFLICT,
            )

        serializer = CampaignEditSerializer(campaign, data=request.data, partial=True)
        if not serializer.is_valid():
            return Response(
                api_response(
                    success=False,
                    message="Error de validación.",
                    data={"errors": serializer.errors},
                ),
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer.save()
        return Response(
            api_response(
                success=True,
                message="Cambios guardados.",
                data={"campaign": CampaignSerializer(campaign).data},
            ),
            status=status.HTTP_200_OK,
        )

    @action(detail=True, methods=["post"], url_path="submit")
    def submit(self, request: Request, pk: int = None) -> Response:
        """
        POST /api/campaigns/{id}/submit/

        Transiciona GENERADO → PENDIENTE_APROBACION.
        Solo rol marketero puede ejecutarlo.
        """
        if request.user.rol != "marketero":
            return Response(
                api_response(
                    success=False,
                    message="Solo el marketero puede enviar al cliente.",
                    data={},
                ),
                status=status.HTTP_403_FORBIDDEN,
            )

        campaign = self.get_object()

        if campaign.estado != CampaignStatus.GENERADO:
            return Response(
                api_response(
                    success=False,
                    message=(
                        f"Solo campañas en estado 'generado' pueden enviarse. "
                        f"Estado actual: '{campaign.estado}'."
                    ),
                    data={},
                ),
                status=status.HTTP_409_CONFLICT,
            )

        try:
            campaign.transition_to(CampaignStatus.PENDIENTE_APROBACION)
        except ValidationError as e:
            return Response(
                api_response(
                    success=False,
                    message=e.message,
                    data={},
                ),
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            api_response(
                success=True,
                message="Campaña enviada al cliente para aprobación.",
                data={"campaign": CampaignSerializer(campaign).data},
            ),
            status=status.HTTP_200_OK,
        )

    @action(detail=False, methods=["get"], url_path="stats")
    def stats(self, request: Request) -> Response:
        """
        GET /api/campaigns/stats/

        Retorna conteo de campañas agrupadas por estado para el usuario
        autenticado (superadmin ve todo, marketero solo las suyas).

        Returns:
            HTTP 200 con conteos por estado.
        """
        qs = self.get_queryset()

        conteos: dict[str, int] = {estado: 0 for estado in CampaignStatus.values}
        for campaign in qs.values("estado"):
            conteos[campaign["estado"]] += 1

        return Response(
            api_response(
                success=True,
                message="Estadísticas de campañas.",
                data={
                    "total": sum(conteos.values()),
                    **conteos,
                },
            ),
            status=status.HTTP_200_OK,
        )
