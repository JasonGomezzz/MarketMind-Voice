"""
MarketMind IA — Campaign Serializer
Validación y serialización del modelo Campaign.
"""

from rest_framework import serializers

from apps.authentication.models import User, UserRole

from .models import Campaign, CampaignPlataforma, CampaignStatus, CampaignTono, CampaignVersion

# TODO: mover a TextChoices en models.py (Sprint refactor)
INDUSTRIA_CHOICES = [
    "tecnologia", "salud", "educacion", "retail",
    "gastronomia", "moda", "finanzas", "entretenimiento", "otro",
]


class CampaignSerializer(serializers.ModelSerializer):
    """
    Serializer principal de Campaign.

    Campos de escritura (requeridos en create):
        titulo, cliente_nombre, industria, tono, plataforma, prompt.

    Campos de solo lectura (devueltos en respuesta):
        id, estado, texto_generado, imagen_url, marketero, fecha_creacion.
    """

    marketero = serializers.StringRelatedField(read_only=True)
    cliente_email = serializers.EmailField(required=True)

    class Meta:
        model = Campaign
        fields = [
            "id",
            "titulo",
            "cliente_nombre",
            "cliente_email",
            "industria",
            "tono",
            "plataforma",
            "prompt",
            "estado",
            "texto_generado",
            "imagen_url",
            "imagen_b64",
            "ia_error_message",
            "feedback_rechazo",
            "email_enviado",
            "enviado_cliente_at",
            "cliente_valoracion",
            "cliente_valoracion_at",
            "rechazos_cliente_count",
            "marketero",
            "fecha_creacion",
        ]
        read_only_fields = [
            "id",
            "estado",
            "texto_generado",
            "imagen_url",
            "imagen_b64",
            "ia_error_message",
            "feedback_rechazo",
            "email_enviado",
            "enviado_cliente_at",
            "cliente_valoracion",
            "cliente_valoracion_at",
            "rechazos_cliente_count",
            "marketero",
            "fecha_creacion",
        ]

    def validate_titulo(self, value: str) -> str:
        """Valida longitud mínima y máxima del título."""
        value = value.strip()
        if len(value) < 5:
            raise serializers.ValidationError("El título debe tener al menos 5 caracteres.")
        if len(value) > 200:
            raise serializers.ValidationError("El título no puede superar los 200 caracteres.")
        return value

    def validate_cliente_nombre(self, value: str) -> str:
        """Valida que el nombre del cliente no esté vacío."""
        value = value.strip()
        if not value:
            raise serializers.ValidationError("El nombre del cliente no puede estar vacío.")
        if len(value) > 150:
            raise serializers.ValidationError(
                "El nombre del cliente no puede superar 150 caracteres."
            )
        return value

    def validate_cliente_email(self, value: str) -> str:
        """Normaliza el email del cliente."""
        return value.strip().lower()

    def validate(self, attrs: dict) -> dict:
        """
        Valida que exista un cliente registrado con ese email.

        El 'cliente_nombre' es libre (el marketero puede usar el nombre del
        negocio/marca, ej. 'Gimnasio Mega Force'); NO tiene que coincidir con
        el nombre de la cuenta. La identidad se ancla en el email, que sí debe
        pertenecer a un usuario con rol cliente (evita enviar campañas a
        destinatarios inexistentes).
        """
        attrs = super().validate(attrs)
        email = attrs.get("cliente_email")
        nombre = attrs.get("cliente_nombre")
        if not email:
            raise serializers.ValidationError(
                {"cliente_email": "El email del cliente es obligatorio."}
            )
        if not nombre:
            raise serializers.ValidationError(
                {"cliente_nombre": "El nombre del cliente es obligatorio."}
            )

        try:
            cliente = User.objects.get(email=email, rol=UserRole.CLIENTE)
        except User.DoesNotExist as exc:
            raise serializers.ValidationError(
                {"cliente_email": "Debe existir un usuario cliente registrado con este email."}
            ) from exc

        # Email normalizado al del cliente registrado; nombre se respeta tal cual.
        attrs["cliente_email"] = cliente.email
        attrs["cliente_nombre"] = nombre.strip()
        return attrs

    def validate_prompt(self, value: str) -> str:
        """Valida longitud mínima y máxima del prompt."""
        value = value.strip()
        if len(value) < 10:
            raise serializers.ValidationError("El prompt debe tener al menos 10 caracteres.")
        if len(value) > 2000:
            raise serializers.ValidationError("El prompt no puede superar los 2000 caracteres.")
        return value

    def validate_industria(self, value: str) -> str:
        """Valida que la industria sea una de las opciones permitidas."""
        value = value.strip().lower()
        if value not in INDUSTRIA_CHOICES:
            raise serializers.ValidationError(
                f"Industria inválida. Opciones: {', '.join(INDUSTRIA_CHOICES)}."
            )
        return value

    def validate_tono(self, value: str) -> str:
        """Valida que el tono sea un valor definido en CampaignTono."""
        value = value.strip().lower()
        if value not in CampaignTono.values:
            raise serializers.ValidationError(
                f"Tono inválido. Opciones: {', '.join(CampaignTono.values)}."
            )
        return value

    def validate_plataforma(self, value: str) -> str:
        """Valida que la plataforma sea un valor definido en CampaignPlataforma."""
        value = value.strip().lower()
        if value not in CampaignPlataforma.values:
            raise serializers.ValidationError(
                f"Plataforma inválida. Opciones: {', '.join(CampaignPlataforma.values)}."
            )
        return value


class CampaignEditSerializer(serializers.ModelSerializer):
    """Serializer para edición de prompt y texto_generado por el marketero."""

    class Meta:
        model = Campaign
        fields = ["prompt", "texto_generado"]

    def validate_prompt(self, value: str) -> str:
        value = value.strip()
        if len(value) < 10:
            raise serializers.ValidationError("El prompt debe tener al menos 10 caracteres.")
        if len(value) > 2000:
            raise serializers.ValidationError("El prompt no puede superar los 2000 caracteres.")
        return value

    def validate_texto_generado(self, value: str) -> str:
        value = value.strip()
        if not value:
            raise serializers.ValidationError("El texto no puede estar vacío.")
        return value


class CampaignVersionSerializer(serializers.ModelSerializer):
    texto_preview = serializers.SerializerMethodField()
    tiene_imagen = serializers.SerializerMethodField()

    class Meta:
        model = CampaignVersion
        fields = [
            'id', 'version_number', 'texto_preview',
            'tiene_imagen', 'imagen_b64', 'created_at',
        ]

    def get_texto_preview(self, obj: CampaignVersion) -> str:
        """Retorna los primeros 200 caracteres del texto para la lista."""
        texto = obj.texto_generado or ''
        return texto[:200] + ('…' if len(texto) > 200 else '')

    def get_tiene_imagen(self, obj: CampaignVersion) -> bool:
        return bool(obj.imagen_b64)
