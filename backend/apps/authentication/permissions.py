"""
MarketMind IA — Role-Based Permissions
Define permisos basados en el rol del usuario extraído del JWT.
Criterio HU2: Marketero accede endpoint admin → HTTP 403.
"""

from rest_framework.permissions import BasePermission
from rest_framework.request import Request
from rest_framework.views import APIView

from .models import UserRole


class IsSuperAdmin(BasePermission):
    """
    Permite acceso solo a usuarios con rol superadmin.

    Criterio HU2: Si el rol no es superadmin → HTTP 403.
    """

    message = "Acceso denegado. Se requiere rol superadmin."

    def has_permission(self, request: Request, view: APIView) -> bool:
        """
        Verifica que el usuario autenticado tenga rol superadmin.

        Args:
            request: Request con usuario autenticado via JWT.
            view: Vista que requiere el permiso.

        Returns:
            True si el usuario es superadmin, False en caso contrario.
        """
        return (
            request.user
            and request.user.is_authenticated
            and request.user.rol == UserRole.SUPERADMIN
        )


class IsMarketero(BasePermission):
    """Permite acceso solo a usuarios con rol marketero."""

    message = "Acceso denegado. Se requiere rol marketero."

    def has_permission(self, request: Request, view: APIView) -> bool:
        """
        Verifica que el usuario autenticado tenga rol marketero.

        Args:
            request: Request con usuario autenticado via JWT.
            view: Vista que requiere el permiso.

        Returns:
            True si el usuario es marketero, False en caso contrario.
        """
        return (
            request.user
            and request.user.is_authenticated
            and request.user.rol == UserRole.MARKETERO
        )


class IsCliente(BasePermission):
    """Permite acceso solo a usuarios con rol cliente."""

    message = "Acceso denegado. Se requiere rol cliente."

    def has_permission(self, request: Request, view: APIView) -> bool:
        """
        Verifica que el usuario autenticado tenga rol cliente.

        Args:
            request: Request con usuario autenticado via JWT.
            view: Vista que requiere el permiso.

        Returns:
            True si el usuario es cliente, False en caso contrario.
        """
        return (
            request.user
            and request.user.is_authenticated
            and request.user.rol == UserRole.CLIENTE
        )


class IsMarketeroOrSuperAdmin(BasePermission):
    """Permite acceso a marketeros y superadmins."""

    message = "Acceso denegado. Se requiere rol marketero o superadmin."

    def has_permission(self, request: Request, view: APIView) -> bool:
        """
        Verifica que el usuario sea marketero o superadmin.

        Args:
            request: Request con usuario autenticado via JWT.
            view: Vista que requiere el permiso.

        Returns:
            True si el usuario tiene el rol requerido.
        """
        return (
            request.user
            and request.user.is_authenticated
            and request.user.rol in [UserRole.MARKETERO, UserRole.SUPERADMIN]
        )


class TokenVersionPermission(BasePermission):
    """
    Valida que el token_version del JWT coincida con el de la BD.
    Invalida tokens cuando un usuario es suspendido (HU18).
    """

    message = "Token inválido. La cuenta fue modificada, vuelva a iniciar sesión."

    def has_permission(self, request: Request, view: APIView) -> bool:
        """
        Compara token_version del JWT contra el valor actual en BD.

        Args:
            request: Request con usuario autenticado via JWT.
            view: Vista que requiere el permiso.

        Returns:
            True si la versión del token es válida.
        """
        if not request.user or not request.user.is_authenticated:
            return False

        # El token_version fue inyectado en el payload por CustomTokenObtainPairSerializer
        token_version_in_jwt = request.auth.get("token_version", 0)
        return request.user.token_version == token_version_in_jwt
