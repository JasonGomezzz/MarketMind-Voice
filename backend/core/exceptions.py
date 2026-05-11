"""
MarketMind IA — Centralized Exception Handler
Todas las respuestas de la API siguen el formato:
    {success: bool, message: str, data: {}}

Registrado en REST_FRAMEWORK['EXCEPTION_HANDLER'] en base.py.
"""

from typing import Any

from django.core.exceptions import PermissionDenied
from django.http import Http404
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import exception_handler


def api_response(
    success: bool,
    message: str,
    data: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    Construye el formato estándar de respuesta de la API.

    Todas las respuestas del sistema DEBEN usar esta función
    para garantizar consistencia en el contrato de la API.

    Args:
        success: True si la operación fue exitosa, False si hubo error.
        message: Mensaje descriptivo para el cliente (humano-legible).
        data: Payload de datos. Nunca None en la respuesta final.

    Returns:
        Dict con formato: {success, message, data}

    Example:
        >>> api_response(True, "Usuario creado.", {"user": {...}})
        {"success": True, "message": "Usuario creado.", "data": {"user": {...}}}
    """
    return {
        "success": success,
        "message": message,
        "data": data if data is not None else {},
    }


def custom_exception_handler(exc: Exception, context: dict) -> Response | None:
    """
    Handler centralizado de excepciones para DRF.

    Intercepta todas las excepciones y las convierte al formato
    estándar {success, message, data} antes de enviar la respuesta.

    Args:
        exc: Excepción capturada por DRF.
        context: Contexto de la vista que lanzó la excepción.

    Returns:
        Response con formato estándar, o None si DRF no maneja la excepción.
    """
    # Primero dejamos que DRF maneje la excepción normalmente
    response = exception_handler(exc, context)

    if response is not None:
        # Extraemos el mensaje del error original de DRF
        original_data = response.data

        # Determinamos el mensaje principal
        if isinstance(original_data, dict):
            # Priorizar campos comunes de error
            if "detail" in original_data:
                message = str(original_data["detail"])
                errors = {}
            else:
                message = "Error de validación en los datos enviados."
                errors = original_data
        elif isinstance(original_data, list):
            message = str(original_data[0]) if original_data else "Error desconocido."
            errors = {}
        else:
            message = str(original_data)
            errors = {}

        response.data = api_response(
            success=False,
            message=message,
            data={"errors": errors} if errors else {},
        )

    # Manejar excepciones de Django que DRF no capta
    elif isinstance(exc, Http404):
        return Response(
            api_response(
                success=False,
                message="El recurso solicitado no existe.",
                data={},
            ),
            status=status.HTTP_404_NOT_FOUND,
        )
    elif isinstance(exc, PermissionDenied):
        return Response(
            api_response(
                success=False,
                message="No tienes permisos para realizar esta acción.",
                data={},
            ),
            status=status.HTTP_403_FORBIDDEN,
        )

    return response
