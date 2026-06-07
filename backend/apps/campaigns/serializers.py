"""
MarketMind IA — Campaign Serializer
Validación y serialización del modelo Campaign.
"""

from rest_framework import serializers

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
            "feedback_rechazo",
            "email_enviado",
            "marketero",
            "fecha_creacion",
        ]
        read_only_fields = [
            "id",
            "estado",
            "texto_generado",
            "imagen_url",
            "imagen_b64",
            "feedback_rechazo",
            "email_enviado",
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
    """Serializer para edición de texto_generado por el marketero (HU10)."""

    class Meta:
        model = Campaign
        fields = ["texto_generado"]

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
