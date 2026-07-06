"""
MarketMind IA — Custom JWT Authentication
Subclase de JWTAuthentication que valida token_version (HU18).

Cuando un SuperAdmin suspende o reactiva un usuario, su token_version
se incrementa en BD. Los JWT emitidos antes contienen el valor anterior,
así que esta clase los rechaza con HTTP 401 — el usuario debe volver
a iniciar sesión (y si está suspendido, el login también fallará).
"""

from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken
from rest_framework_simplejwt.tokens import Token

from .models import User


class TokenVersionJWTAuthentication(JWTAuthentication):
    """
    JWTAuthentication que además valida que token_version del JWT
    coincida con el valor actual en la BD.

    Aplicada como DEFAULT_AUTHENTICATION_CLASSES, cubre TODOS los
    endpoints que usen JWT — incluyendo views con permission_classes
    explícito, porque la validación ocurre en la capa de autenticación.
    """

    def get_user(self, validated_token: Token) -> User:
        """
        Recupera el usuario y verifica token_version.

        Args:
            validated_token: Token JWT ya verificado por simplejwt.

        Returns:
            Instancia del usuario asociado al token.

        Raises:
            InvalidToken: Si el token_version del JWT no coincide con BD.
        """
        user = super().get_user(validated_token)

        token_version_in_jwt = validated_token.get("token_version", 0)
        if user.token_version != token_version_in_jwt:
            raise InvalidToken(
                "La cuenta fue modificada por el administrador. "
                "Vuelva a iniciar sesión."
            )

        return user
