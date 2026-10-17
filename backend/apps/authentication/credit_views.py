"""
Solicitudes de créditos con aprobación auditada del superadmin.

Adaptado de la rama de Piero (79bf0db7):
- El marketero solicita (una pendiente a la vez); el superadmin aprueba con
  una cantidad o rechaza. Se registra quién, cuándo, cuánto y el saldo final.
- El saldo se suma con services.credit_service.agregar_creditos (UPDATE con
  F(), sin pisar cobros concurrentes) en vez de un UPDATE propio.
- Respuestas con el formato estándar {success, message, data}.

Endpoints:
    GET/POST /api/auth/credit-requests/          (marketero)
    GET      /api/admin/credit-requests/?estado=  (superadmin)
    PATCH    /api/admin/credit-requests/{id}/     (superadmin)
"""

from django.db import IntegrityError, transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import serializers, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from core.exceptions import api_response
from services.credit_service import agregar_creditos

from .models import CreditRequest, CreditRequestStatus, User
from .permissions import IsMarketero, IsSuperAdmin

MAX_CREDITOS_POR_SOLICITUD = 10000
LIMITE_LISTADO = 100


class CreditRequestSerializer(serializers.ModelSerializer):
    solicitante_email = serializers.EmailField(source="solicitante.email", read_only=True)
    solicitante_nombre = serializers.CharField(source="solicitante.nombre", read_only=True)
    saldo_actual = serializers.IntegerField(source="solicitante.tokens_disponibles", read_only=True)
    resuelta_por = serializers.SerializerMethodField()

    class Meta:
        model = CreditRequest
        fields = [
            "id",
            "solicitante_email",
            "solicitante_nombre",
            "saldo_actual",
            "motivo",
            "estado",
            "creditos_otorgados",
            "saldo_resultante",
            "nota_resolucion",
            "resuelta_por",
            "resuelta_en",
            "fecha_creacion",
        ]
        read_only_fields = fields

    def get_resuelta_por(self, obj: CreditRequest) -> str | None:
        return obj.resuelta_por.nombre if obj.resuelta_por else None


class NuevaSolicitudSerializer(serializers.Serializer):
    motivo = serializers.CharField(max_length=300, required=False, allow_blank=True, default="")


class DecisionSerializer(serializers.Serializer):
    estado = serializers.ChoiceField(
        choices=[CreditRequestStatus.APROBADA, CreditRequestStatus.RECHAZADA],
        error_messages={"invalid_choice": "La decisión debe ser 'aprobada' o 'rechazada'."},
    )
    creditos = serializers.IntegerField(
        min_value=1, max_value=MAX_CREDITOS_POR_SOLICITUD, required=False
    )
    nota = serializers.CharField(max_length=300, required=False, allow_blank=True, default="")

    def to_internal_value(self, data):
        # IntegerField convierte true en 1: un booleano no es una cantidad de créditos.
        if hasattr(data, "get") and isinstance(data.get("creditos"), bool):
            raise serializers.ValidationError({"creditos": "Indica un número entero de créditos."})
        return super().to_internal_value(data)

    def validate(self, attrs):
        if attrs["estado"] == CreditRequestStatus.APROBADA and "creditos" not in attrs:
            raise serializers.ValidationError({"creditos": "Indica cuántos créditos añadir."})
        if attrs["estado"] == CreditRequestStatus.RECHAZADA and "creditos" in attrs:
            raise serializers.ValidationError({"creditos": "Al rechazar no se añaden créditos."})
        return attrs


def _con_relaciones():
    return CreditRequest.objects.select_related("solicitante", "resuelta_por")


def _error(message: str, code: int, data: dict | None = None) -> Response:
    return Response(api_response(success=False, message=message, data=data or {}), status=code)


class MyCreditRequestsView(APIView):
    """GET: mis solicitudes recientes. POST {motivo?}: pedir créditos al superadmin."""

    permission_classes = [IsAuthenticated, IsMarketero]

    def get(self, request: Request) -> Response:
        solicitudes = list(_con_relaciones().filter(solicitante=request.user)[:20])
        pendiente = next((s for s in solicitudes if s.estado == CreditRequestStatus.PENDIENTE), None)
        return Response(
            api_response(
                success=True,
                message="Solicitudes de créditos.",
                data={
                    "solicitudes": CreditRequestSerializer(solicitudes, many=True).data,
                    "pendiente": CreditRequestSerializer(pendiente).data if pendiente else None,
                },
            ),
            status=status.HTTP_200_OK,
        )

    def post(self, request: Request) -> Response:
        payload = NuevaSolicitudSerializer(data=request.data)
        if not payload.is_valid():
            return _error("Datos inválidos.", status.HTTP_400_BAD_REQUEST, {"errors": payload.errors})

        with transaction.atomic():
            # Bloquear la fila del usuario serializa los dobles clics entre procesos.
            User.objects.select_for_update().filter(pk=request.user.pk).first()
            solicitud = CreditRequest.objects.filter(
                solicitante=request.user, estado=CreditRequestStatus.PENDIENTE
            ).first()
            creada = solicitud is None
            if creada:
                try:
                    with transaction.atomic():
                        solicitud = CreditRequest.objects.create(
                            solicitante=request.user, motivo=payload.validated_data["motivo"].strip()
                        )
                except IntegrityError:  # la restricción única ganó la carrera
                    creada = False
                    solicitud = CreditRequest.objects.get(
                        solicitante=request.user, estado=CreditRequestStatus.PENDIENTE
                    )

        solicitud = _con_relaciones().get(pk=solicitud.pk)
        return Response(
            api_response(
                success=True,
                message=(
                    "Solicitud enviada al superadmin." if creada else "Ya tienes una solicitud pendiente."
                ),
                data={"solicitud": CreditRequestSerializer(solicitud).data},
            ),
            status=status.HTTP_201_CREATED if creada else status.HTTP_200_OK,
        )


class AdminCreditRequestListView(APIView):
    """GET ?estado=pendiente|aprobada|rechazada — solicitudes de todos (las 100 más recientes)."""

    permission_classes = [IsAuthenticated, IsSuperAdmin]

    def get(self, request: Request) -> Response:
        qs = _con_relaciones()
        estado = request.query_params.get("estado")
        if estado:
            if estado not in CreditRequestStatus.values:
                return _error(
                    "Estado inválido.",
                    status.HTTP_400_BAD_REQUEST,
                    {"estados_validos": CreditRequestStatus.values},
                )
            qs = qs.filter(estado=estado)
        return Response(
            api_response(
                success=True,
                message="Solicitudes de créditos.",
                data={
                    "solicitudes": CreditRequestSerializer(qs[:LIMITE_LISTADO], many=True).data,
                    "pendientes": CreditRequest.objects.filter(
                        estado=CreditRequestStatus.PENDIENTE
                    ).count(),
                },
            ),
            status=status.HTTP_200_OK,
        )


class AdminCreditRequestDetailView(APIView):
    """PATCH {estado: aprobada|rechazada, creditos?, nota?} — resolver una solicitud."""

    permission_classes = [IsAuthenticated, IsSuperAdmin]

    def patch(self, request: Request, pk: int) -> Response:
        payload = DecisionSerializer(data=request.data)
        if not payload.is_valid():
            return _error("Decisión inválida.", status.HTTP_400_BAD_REQUEST, {"errors": payload.errors})
        decision = payload.validated_data

        with transaction.atomic():
            solicitud = get_object_or_404(CreditRequest.objects.select_for_update(), pk=pk)
            if solicitud.estado != CreditRequestStatus.PENDIENTE:
                return _error("Esta solicitud ya fue resuelta.", status.HTTP_409_CONFLICT)
            solicitante = User.objects.select_for_update().get(pk=solicitud.solicitante_id)
            if not solicitante.is_active:
                return _error(
                    "La cuenta está suspendida. Reactívala antes de resolver la solicitud.",
                    status.HTTP_409_CONFLICT,
                )

            if decision["estado"] == CreditRequestStatus.APROBADA:
                agregar_creditos(solicitante, decision["creditos"])
                solicitud.creditos_otorgados = decision["creditos"]
                solicitud.saldo_resultante = solicitante.tokens_disponibles
            solicitud.estado = decision["estado"]
            solicitud.nota_resolucion = decision["nota"].strip()
            solicitud.resuelta_por = request.user
            solicitud.resuelta_en = timezone.now()
            solicitud.save(
                update_fields=[
                    "estado",
                    "creditos_otorgados",
                    "saldo_resultante",
                    "nota_resolucion",
                    "resuelta_por",
                    "resuelta_en",
                ]
            )

        solicitud = _con_relaciones().get(pk=solicitud.pk)
        aprobada = solicitud.estado == CreditRequestStatus.APROBADA
        return Response(
            api_response(
                success=True,
                message=(
                    f"Solicitud aprobada: +{solicitud.creditos_otorgados} créditos."
                    if aprobada
                    else "Solicitud rechazada."
                ),
                data={"solicitud": CreditRequestSerializer(solicitud).data},
            ),
            status=status.HTTP_200_OK,
        )
