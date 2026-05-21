"""
MarketMind IA — Authentication Views
Endpoints: POST /api/auth/register/ y POST /api/auth/logout/
Token endpoints provistos por simplejwt directamente en urls.py.
"""

from typing import Any

from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken

from core.exceptions import api_response
from .serializers import RegisterSerializer, UserResponseSerializer
from .throttles import RegisterRateThrottle


class RegisterView(APIView):
    """
    POST /api/auth/register/

    Registra un nuevo usuario en el sistema.
    Acceso público (no requiere autenticación).

    Criterios HU1:
    - Email único → HTTP 400 "El email ya está en uso"
    - Email inválido → HTTP 400 campo específico
    - Rol inválido → HTTP 400 con valores válidos
    - Password < 8 chars → HTTP 400 política de contraseñas
    - Datos correctos → HTTP 201
    """

    permission_classes = [AllowAny]
    throttle_classes = [RegisterRateThrottle]  # 5 intentos / 10 min

    def post(self, request: Request) -> Response:
        """
        Registra un nuevo usuario.

        Args:
            request: Request con body {email, nombre, password, rol}.

        Returns:
            Response HTTP 201 con datos del usuario creado.
            Response HTTP 400 si hay errores de validación.
        """
        serializer = RegisterSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(
                api_response(
                    success=False,
                    message="Error de validación en los datos enviados.",
                    data=serializer.errors,
                ),
                status=status.HTTP_400_BAD_REQUEST,
            )

        user = serializer.save()
        user_data = UserResponseSerializer(user).data

        return Response(
            api_response(
                success=True,
                message="Usuario registrado exitosamente.",
                data={"user": user_data},
            ),
            status=status.HTTP_201_CREATED,
        )


class LogoutView(APIView):
    """
    POST /api/auth/logout/

    Invalida el refresh token del usuario (JWT Blacklist).
    Requiere autenticación con access token válido.
    """

    permission_classes = [IsAuthenticated]

    def post(self, request: Request) -> Response:
        """
        Agrega el refresh token a la blacklist de simplejwt.

        Args:
            request: Request con body {refresh: "<refresh_token>"}.

        Returns:
            Response HTTP 200 si el logout fue exitoso.
            Response HTTP 400 si el token es inválido.
        """
        refresh_token = request.data.get("refresh")

        if not refresh_token:
            return Response(
                api_response(
                    success=False,
                    message="Se requiere el refresh token para hacer logout.",
                    data={},
                ),
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            token = RefreshToken(refresh_token)
            token.blacklist()

            return Response(
                api_response(
                    success=True,
                    message="Sesión cerrada exitosamente.",
                    data={},
                ),
                status=status.HTTP_200_OK,
            )
        except TokenError:
            return Response(
                api_response(
                    success=False,
                    message="Token inválido o expirado.",
                    data={},
                ),
                status=status.HTTP_400_BAD_REQUEST,
            )


class MeView(APIView):
    """
    GET /api/auth/me/
    tokens_disponibles cambia tras cada generación — no puede leerse del JWT.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request: Request) -> Response:
        serializer = UserResponseSerializer(request.user)
        return Response(
            api_response(
                success=True,
                message="Datos del usuario autenticado.",
                data={"user": serializer.data},
            ),
            status=status.HTTP_200_OK,
        )
