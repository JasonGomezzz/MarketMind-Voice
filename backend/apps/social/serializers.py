from rest_framework import serializers

from .models import Publication, PublicationMetric, SocialConnection


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


class PublicationMetricSerializer(serializers.ModelSerializer):
    class Meta:
        model = PublicationMetric
        fields = [
            "me_gusta", "comentarios", "compartidos", "guardados",
            "alcance", "vistas", "interacciones", "obtenida_at",
        ]
        read_only_fields = fields


class PublicationSerializer(serializers.ModelSerializer):
    campaign_titulo = serializers.CharField(source="campaign.titulo", read_only=True)
    ultima_metrica = serializers.SerializerMethodField()

    class Meta:
        model = Publication
        fields = [
            "id", "campaign", "campaign_titulo", "red", "cuenta_nombre", "estado", "permalink",
            "error", "intentos", "version_aprobada", "publicado_at", "fecha_creacion", "ultima_metrica",
        ]
        read_only_fields = fields

    def get_ultima_metrica(self, obj: Publication):
        # Usa la precarga de metrics_service.con_ultima_metrica si existe.
        ordenadas = getattr(obj, "metricas_ordenadas", None)
        metrica = ordenadas[0] if ordenadas else (None if ordenadas is not None else obj.metricas.first())
        return PublicationMetricSerializer(metrica).data if metrica else None
