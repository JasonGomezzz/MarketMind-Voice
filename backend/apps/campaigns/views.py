"""
MarketMind IA — Campaign Views
Endpoint REST para crear, listar y gestionar campañas publicitarias.
"""

import re
from datetime import timedelta
from typing import Any

from django.core.cache import cache
from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Avg, Count, DurationField, ExpressionWrapper, F
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.template.loader import render_to_string
from django.utils import timezone
from rest_framework import generics, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView
from weasyprint import HTML as WeasyHTML

from apps.authentication.permissions import IsSuperAdmin
from core.exceptions import api_response
from services.n8n_service import trigger_ia_generation
from services.version_service import save_campaign_version

from .models import Campaign, CampaignStatus, CampaignVersion
from .permissions import N8nCallbackPermission
from .serializers import CampaignEditSerializer, CampaignSerializer, CampaignVersionSerializer


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

        Crea una campaña en BORRADOR y dispara la generación IA de forma asíncrona.
        Django responde HTTP 202 inmediatamente; el resultado llega por callback n8n.

        Returns:
            HTTP 202 — campaña creada, generación en proceso.
            HTTP 400 — errores de validación.
            HTTP 402 — sin tokens disponibles.
            HTTP 403 — rol no autorizado.
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

        # Recargar user para reflejar cambios de tokens hechos en el servicio
        request.user.refresh_from_db()
        resultado = trigger_ia_generation(campaign)

        # Recargar campaña — el servicio pudo haber cambiado estado y texto
        campaign.refresh_from_db()

        if resultado.get("mock"):
            message = "Campaña creada y contenido generado (modo mock)."
        elif resultado["dispatched"]:
            message = "Campaña creada. Generando contenido IA en segundo plano..."
        else:
            message = "Campaña creada como borrador. El servicio IA no está disponible."

        return Response(
            api_response(
                success=True,
                message=message,
                data={"campaign": CampaignSerializer(campaign).data},
            ),
            status=status.HTTP_202_ACCEPTED,
        )

    @action(detail=True, methods=["post"], url_path="generate")
    def generate(self, request: Request, pk: int = None) -> Response:
        """
        POST /api/campaigns/{id}/generate/

        Dispara (o re-dispara) la generación IA para una campaña en BORRADOR.
        Máximo 3 intentos por campaña.

        Returns:
            HTTP 202 — generación en proceso.
            HTTP 402 — sin tokens disponibles.
            HTTP 409 — estado incorrecto o intentos agotados.
        """
        if request.user.rol != "marketero":
            return Response(
                api_response(success=False, message="Solo el marketero puede generar.", data={}),
                status=status.HTTP_403_FORBIDDEN,
            )

        campaign = self.get_object()

        if campaign.estado != CampaignStatus.BORRADOR:
            return Response(
                api_response(
                    success=False,
                    message=f"Solo campañas en 'borrador' pueden generarse. Estado actual: '{campaign.estado}'.",
                    data={},
                ),
                status=status.HTTP_409_CONFLICT,
            )

        if request.user.tokens_disponibles <= 0:
            return Response(
                api_response(
                    success=False,
                    message="Sin tokens disponibles. Contacta al administrador.",
                    data={"tokens_disponibles": 0},
                ),
                status=status.HTTP_402_PAYMENT_REQUIRED,
            )

        request.user.refresh_from_db()
        resultado = trigger_ia_generation(campaign)
        campaign.refresh_from_db()

        if not resultado["dispatched"]:
            return Response(
                api_response(
                    success=False,
                    message=resultado.get("error", "No se pudo iniciar la generación."),
                    data={"campaign": CampaignSerializer(campaign).data},
                ),
                status=status.HTTP_409_CONFLICT,
            )

        if resultado.get("mock"):
            message = "Contenido generado (modo mock)."
        else:
            message = "Generación IA iniciada. El resultado llegará en breve."

        return Response(
            api_response(
                success=True,
                message=message,
                data={"campaign": CampaignSerializer(campaign).data},
            ),
            status=status.HTTP_202_ACCEPTED,
        )

    @action(detail=True, methods=["post"], url_path="regenerate")
    def regenerate(self, request: Request, pk: int = None) -> Response:
        """
        POST /api/campaigns/{id}/regenerate/

        Regenera el contenido IA de una campaña que ya fue rechazada o falló.
        La campaña debe estar en BORRADOR (estado tras rechazo o fallo previo).
        Máximo 3 intentos acumulados.

        Returns:
            HTTP 202 — regeneración en proceso.
            HTTP 402 — sin tokens disponibles.
            HTTP 409 — estado incorrecto o intentos agotados.
        """
        if request.user.rol != "marketero":
            return Response(
                api_response(success=False, message="Solo el marketero puede regenerar.", data={}),
                status=status.HTTP_403_FORBIDDEN,
            )

        campaign = self.get_object()

        if campaign.estado != CampaignStatus.BORRADOR:
            return Response(
                api_response(
                    success=False,
                    message=f"Solo campañas en 'borrador' pueden regenerarse. Estado actual: '{campaign.estado}'.",
                    data={},
                ),
                status=status.HTTP_409_CONFLICT,
            )

        if request.user.tokens_disponibles <= 0:
            return Response(
                api_response(
                    success=False,
                    message="Sin tokens disponibles. Contacta al administrador.",
                    data={"tokens_disponibles": 0},
                ),
                status=status.HTTP_402_PAYMENT_REQUIRED,
            )

        request.user.refresh_from_db()
        resultado = trigger_ia_generation(campaign)
        campaign.refresh_from_db()

        if not resultado["dispatched"]:
            return Response(
                api_response(
                    success=False,
                    message=resultado.get("error", "No se pudo iniciar la regeneración."),
                    data={"campaign": CampaignSerializer(campaign).data},
                ),
                status=status.HTTP_409_CONFLICT,
            )

        if resultado.get("mock"):
            message = "Contenido regenerado (modo mock)."
        else:
            message = "Regeneración IA iniciada. El resultado llegará en breve."

        return Response(
            api_response(
                success=True,
                message=message,
                data={"campaign": CampaignSerializer(campaign).data},
            ),
            status=status.HTTP_202_ACCEPTED,
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

        Retorna conteo de campañas agrupadas por estado.
        Resultado cacheado 30s en Redis por usuario; el signal post_save
        de Campaign invalida la caché cuando cambia una campaña.

        Returns:
            HTTP 200 con conteos por estado.
        """
        cache_key = f"campaign_stats_{request.user.id}"
        cached_data = cache.get(cache_key)

        if cached_data is not None:
            return Response(
                api_response(
                    success=True,
                    message="Estadísticas de campañas.",
                    data=cached_data,
                ),
                status=status.HTTP_200_OK,
            )

        qs = self.get_queryset()
        conteos: dict[str, int] = {estado: 0 for estado in CampaignStatus.values}
        for campaign in qs.values("estado"):
            conteos[campaign["estado"]] += 1

        data = {
            "total": sum(conteos.values()),
            **conteos,
        }
        cache.set(cache_key, data, timeout=30)

        return Response(
            api_response(
                success=True,
                message="Estadísticas de campañas.",
                data=data,
            ),
            status=status.HTTP_200_OK,
        )


class IaResultCallbackView(APIView):
    """
    POST /api/campaigns/webhook/ia-result/

    Endpoint de callback para n8n. Recibe el resultado de la generación IA
    (éxito o fallo) y actualiza el estado de la campaña en consecuencia.

    Autenticación: N8nCallbackPermission (valida n8n_callback_token UUID).
    No requiere JWT — diseñado para llamadas machine-to-machine desde n8n.

    Body éxito:
        {n8n_callback_token, success: true, copy: str}
    Body fallo:
        {n8n_callback_token, success: false, error: str}
    """

    authentication_classes: list = []
    permission_classes = [N8nCallbackPermission]

    def post(self, request: Request) -> Response:
        """
        Procesa el resultado de generación IA enviado por n8n.

        Éxito: PENDIENTE_IA → GENERADO, guarda texto_generado.
        Fallo: PENDIENTE_IA → BORRADOR, devuelve 1 token al marketero.
        Todo en transaction.atomic() para consistencia.
        """
        token = request.data.get("n8n_callback_token")
        success = request.data.get("success", False)

        try:
            with transaction.atomic():
                campaign = (
                    Campaign.objects.select_related("marketero")
                    .select_for_update()
                    .get(n8n_callback_token=token)
                )

                if success:
                    save_campaign_version(campaign)
                    copy = request.data.get("copy", "")
                    imagen_b64 = request.data.get("imagen_b64")
                    campaign.texto_generado = copy
                    campaign.imagen_b64 = imagen_b64
                    campaign.save(update_fields=["texto_generado", "imagen_b64", "fecha_actualizacion"])
                    campaign.transition_to(CampaignStatus.GENERADO)

                    return Response(
                        api_response(
                            success=True,
                            message="Contenido IA generado y guardado.",
                            data={
                                "campaign_id": campaign.id,
                                "estado": campaign.estado,
                                "tiene_imagen": imagen_b64 is not None,
                            },
                        ),
                        status=status.HTTP_200_OK,
                    )

                # Fallo: devolver token + estado → borrador
                error_msg = request.data.get("error", "Error desconocido en n8n/Gemini.")
                campaign.ia_error_message = error_msg
                campaign.save(update_fields=["ia_error_message", "fecha_actualizacion"])

                user = campaign.marketero
                user.tokens_disponibles += 1
                user.save(update_fields=["tokens_disponibles"])

                campaign.transition_to(CampaignStatus.BORRADOR)

                return Response(
                    api_response(
                        success=False,
                        message="Generación IA fallida. Token devuelto al usuario.",
                        data={
                            "campaign_id": campaign.id,
                            "estado": campaign.estado,
                            "error": error_msg,
                        },
                    ),
                    status=status.HTTP_200_OK,
                )

        except Campaign.DoesNotExist:
            return Response(
                api_response(success=False, message="Campaña no encontrada.", data={}),
                status=status.HTTP_404_NOT_FOUND,
            )
        except ValidationError as e:
            return Response(
                api_response(success=False, message=str(e.message), data={}),
                status=status.HTTP_409_CONFLICT,
            )


class EmailSentCallbackView(APIView):
    """
    POST /api/campaigns/webhook/email-sent/

    Callback de n8n tras enviar email vía Resend (HU16). Solo el evento
    pendiente_aprobacion persiste flag (email_enviado=True); HU17 no incluye
    callback_url en el payload disparador y por lo tanto nunca llega aquí.

    Autenticación: N8nCallbackPermission (valida n8n_callback_token UUID).

    Body:
        {n8n_callback_token: str, success: bool, event_type: str}
    """

    authentication_classes: list = []
    permission_classes = [N8nCallbackPermission]

    def post(self, request: Request) -> Response:
        """Marca email_enviado=True si el envío Resend fue exitoso (HU16)."""
        token = request.data.get("n8n_callback_token")
        success = bool(request.data.get("success", False))
        event_type = request.data.get("event_type")

        try:
            campaign = Campaign.objects.get(n8n_callback_token=token)
        except Campaign.DoesNotExist:
            return Response(
                api_response(success=False, message="Campaña no encontrada.", data={}),
                status=status.HTTP_404_NOT_FOUND,
            )

        if success and event_type == "pendiente_aprobacion":
            campaign.email_enviado = True
            campaign.save(update_fields=["email_enviado", "fecha_actualizacion"])

        return Response(
            api_response(
                success=True,
                message="Callback de email procesado.",
                data={"campaign_id": campaign.id, "email_enviado": campaign.email_enviado},
            ),
            status=status.HTTP_200_OK,
        )


_PERIOD_DAYS: dict[str, int] = {"week": 7, "month": 30, "quarter": 90}


class AdminAnalyticsView(APIView):
    """
    GET /api/admin/analytics/?period=week|month|quarter

    Dashboard de analytics para superadmin.
    Devuelve KPIs, campañas por marketero y distribución de estados
    para el periodo seleccionado.

    Requiere rol superadmin — HTTP 403 para cualquier otro rol.
    """

    permission_classes = [IsAuthenticated, IsSuperAdmin]

    def get(self, request: Request) -> Response:
        """
        Calcula métricas agregadas de campañas para el periodo indicado.

        Query params:
            period: week | month | quarter (default: month)

        Returns:
            HTTP 200 con kpi, campanas_por_marketero y estados_globales.
        """
        period = request.query_params.get("period", "month")
        days = _PERIOD_DAYS.get(period, 30)
        desde = timezone.now() - timedelta(days=days)

        qs = Campaign.objects.filter(fecha_creacion__gte=desde)

        # KPIs
        total = qs.count()
        aprobadas = qs.filter(estado=CampaignStatus.APROBADO).count()
        tasa = round(aprobadas / total * 100, 1) if total > 0 else 0

        duracion_avg = (
            qs.filter(estado=CampaignStatus.APROBADO)
            .annotate(
                duracion=ExpressionWrapper(
                    F("fecha_actualizacion") - F("fecha_creacion"),
                    output_field=DurationField(),
                )
            )
            .aggregate(avg=Avg("duracion"))["avg"]
        )
        dias_promedio = (
            round(duracion_avg.total_seconds() / 86400, 1) if duracion_avg else None
        )

        # Campañas por marketero
        por_marketero = list(
            qs.values("marketero__nombre")
            .annotate(total=Count("id"))
            .order_by("-total")
        )

        # Distribución de estados (todos los estados con conteo 0 si no hay datos)
        conteos: dict[str, int] = {s: 0 for s in CampaignStatus.values}
        for row in qs.values("estado").annotate(total=Count("id")):
            conteos[row["estado"]] = row["total"]

        return Response(
            api_response(
                success=True,
                message="Analytics generadas.",
                data={
                    "periodo": period,
                    "kpi": {
                        "total_campanas": total,
                        "tasa_aprobacion": tasa,
                        "tiempo_promedio_aprobacion_dias": dias_promedio,
                    },
                    "campanas_por_marketero": [
                        {"marketero": r["marketero__nombre"], "total": r["total"]}
                        for r in por_marketero
                    ],
                    "estados_globales": [
                        {"estado": k, "total": v} for k, v in conteos.items()
                    ],
                },
            ),
            status=status.HTTP_200_OK,
        )


class CampaignVersionListView(generics.ListAPIView):
    """
    GET /api/campaigns/{campaign_id}/versions/

    Retorna las últimas 5 versiones de una campaña.
    Solo el owner o un superadmin puede acceder.
    """

    serializer_class = CampaignVersionSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = None

    def get_queryset(self):
        campaign_id = self.kwargs['campaign_id']
        campaign = get_object_or_404(
            Campaign.objects.select_related('marketero'),
            pk=campaign_id,
        )
        user = self.request.user
        if campaign.marketero != user and user.rol != 'superadmin':
            raise PermissionDenied("No tienes acceso a esta campaña.")
        return CampaignVersion.objects.filter(campaign=campaign)

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response({
            'success': True,
            'message': 'Versiones obtenidas correctamente.',
            'data': serializer.data,
        })


class CampaignExportPDFView(APIView):
    """
    GET /api/campaigns/{campaign_id}/export-pdf/

    Genera y retorna un PDF descargable de una campaña aprobada.
    Solo el owner (marketero) de la campaña o un superadmin puede acceder.
    Requiere estado == 'aprobado'. Retorna application/pdf como attachment.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request: Request, campaign_id: int) -> HttpResponse:
        """Renderiza el template HTML de la campaña y lo convierte a PDF con WeasyPrint."""
        campaign = get_object_or_404(
            Campaign.objects.select_related("marketero"),
            pk=campaign_id,
        )
        user = request.user
        if campaign.marketero != user and user.rol != "superadmin":
            return Response(
                {"success": False, "message": "No tienes acceso a esta campaña."},
                status=status.HTTP_403_FORBIDDEN,
            )
        if campaign.estado != CampaignStatus.APROBADO:
            return Response(
                {"success": False, "message": "Solo se pueden exportar campañas aprobadas."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        context = {
            "campaign": campaign,
            "fecha_exportacion": timezone.localtime().strftime("%d/%m/%Y %H:%M"),
        }
        html_string = render_to_string("campaigns/campaign_pdf.html", context)
        try:
            pdf_bytes = WeasyHTML(
                string=html_string,
                base_url=request.build_absolute_uri("/"),
            ).write_pdf()
        except Exception:
            # imagen_b64 corrupta — regenerar sin imagen y sin romper el flujo
            original_imagen = campaign.imagen_b64
            campaign.imagen_b64 = None
            html_string_sin_imagen = render_to_string(
                "campaigns/campaign_pdf.html", context
            )
            campaign.imagen_b64 = original_imagen  # restaurar en memoria
            pdf_bytes = WeasyHTML(
                string=html_string_sin_imagen,
                base_url=request.build_absolute_uri("/"),
            ).write_pdf()

        safe_title = re.sub(r"[^\w\-]", "_", campaign.titulo[:40])
        response = HttpResponse(pdf_bytes, content_type="application/pdf")
        response["Content-Disposition"] = f'attachment; filename="campana_{safe_title}.pdf"'
        return response
