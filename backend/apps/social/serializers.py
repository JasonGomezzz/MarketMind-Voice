from rest_framework import serializers

from .models import Publication, SocialConnection


class SocialConnectionSerializer(serializers.ModelSerializer):
    """Nunca incluye el token: solo lo necesario para mostrar y elegir destino."""

    propietario_email = serializers.EmailField(source="usuario.email", read_only=True)
    propietario_rol = serializers.CharField(source="usuario.rol", read_only=True)

    class Meta:
        model = SocialConnection
        fields = [
            "id", "red", "cuenta_nombre", "estado",
            "propietario_email", "propietario_rol", "fecha_creacion",
        ]
        read_only_fields = fields


class PublicationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Publication
        fields = [
            "id", "campaign", "red", "cuenta_nombre", "estado", "permalink",
            "error", "intentos", "version_aprobada", "publicado_at", "fecha_creacion",
        ]
        read_only_fields = fields
