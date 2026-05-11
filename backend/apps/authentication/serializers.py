"""
MarketMind IA — Authentication Serializers
Maneja registro de usuarios y JWT con campo 'role' en payload.
Criterios HU1 y HU2.
"""

from typing import Any

from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.tokens import Token

from .models import User, UserRole


class RegisterSerializer(serializers.ModelSerializer):
    """
    Serializer para registro de nuevos usuarios.

    Valida:
    - Email único en BD (HU1: email duplicado → HTTP 400)
    - Formato de email válido (HU1: formato inválido → HTTP 400)
    - Rol dentro de los valores permitidos (HU1: rol inválido → HTTP 400)
    - Password mínimo 8 caracteres (HU1: password corto → HTTP 400)
    """

    password = serializers.CharField(
        write_only=True,
        min_length=8,
        error_messages={
            "min_length": "La contraseña debe tener al menos 8 caracteres.",
        },
    )
    rol = serializers.ChoiceField(
        choices=UserRole.choices,
        error_messages={
            "invalid_choice": (
                "Rol inválido. Valores permitidos: "
                f"{', '.join(UserRole.values)}."
            ),
        },
    )

    class Meta:
        model = User
        fields = ["email", "nombre", "password", "rol"]
        extra_kwargs = {
            "email": {
                "error_messages": {
                    "invalid": "El formato del email es inválido.",
                    "unique": "El email ya está en uso.",
                }
            },
        }

    def validate_password(self, value: str) -> str:
        """
        Aplica los validadores de Django configurados en AUTH_PASSWORD_VALIDATORS.

        Args:
            value: Contraseña en texto plano.

        Returns:
            La contraseña si pasa todas las validaciones.

        Raises:
            ValidationError: Si la contraseña no cumple los requisitos.
        """
        validate_password(value)
        return value

    def create(self, validated_data: dict[str, Any]) -> User:
        """
        Crea el usuario llamando al manager que encripta la contraseña.

        Args:
            validated_data: Datos validados del serializer.

        Returns:
            Instancia del usuario creado en BD.
        """
        return User.objects.create_user(
            email=validated_data["email"],
            password=validated_data["password"],
            nombre=validated_data["nombre"],
            rol=validated_data["rol"],
        )


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    Extiende simplejwt para incluir el campo 'role' en el payload del JWT.

    Criterio HU2: Login → access_token + refresh_token + role en payload.
    """

    @classmethod
    def get_token(cls, user: User) -> Token:
        """
        Agrega claims personalizados al token JWT.

        Args:
            user: Instancia del usuario autenticado.

        Returns:
            Token JWT con claims adicionales: role, nombre, token_version.
        """
        token = super().get_token(user)

        # Claims adicionales en el payload
        token["role"] = user.rol
        token["nombre"] = user.nombre
        token["token_version"] = user.token_version  # Para invalidación en HU18

        return token

    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
        """
        Agrega campos extra a la respuesta del login.

        Args:
            attrs: Credenciales del usuario.

        Returns:
            Dict con access, refresh, role y nombre del usuario.
        """
        data = super().validate(attrs)

        # Info extra en la respuesta (no solo en el payload del token)
        data["role"] = self.user.rol
        data["nombre"] = self.user.nombre

        return data


class UserResponseSerializer(serializers.ModelSerializer):
    """
    Serializer de solo lectura para representar datos del usuario en respuestas.
    Nunca expone campos sensibles como password o token_version.
    """

    class Meta:
        model = User
        fields = ["id", "email", "nombre", "rol", "is_active", "fecha_creacion"]
        read_only_fields = fields
