"""
MarketMind Voice — Cuentas sociales conectadas y publicaciones.

Django es dueño de la identidad social: los tokens de Meta se guardan
cifrados aquí y nunca salen hacia n8n, React ni Kotlin.

Una Publication congela el copy y la imagen en el momento de la aprobación:
se publica exactamente lo que el cliente aprobó, aunque la campaña cambie
después o su historial de versiones rote.
"""

from django.conf import settings
from django.db import models

from apps.campaigns.models import Campaign


class RedSocial(models.TextChoices):
    INSTAGRAM = "instagram", "Instagram"
    FACEBOOK = "facebook", "Facebook"


class ConexionEstado(models.TextChoices):
    ACTIVA = "activa", "Activa"
    DESCONECTADA = "desconectada", "Desconectada"


class SocialConnection(models.Model):
    """Cuenta de Instagram o página de Facebook autorizada por su dueño vía OAuth."""

    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="conexiones_sociales",
        help_text="Quien autorizó la cuenta (cliente dueño o marketero que la administra).",
    )
    red = models.CharField(max_length=20, choices=RedSocial.choices)
    cuenta_id = models.CharField(
        max_length=64,
        help_text="ID en Meta: página de Facebook o cuenta de Instagram profesional.",
    )
    cuenta_nombre = models.CharField(max_length=150, help_text="Nombre de la página o @usuario.")
    pagina_id = models.CharField(
        max_length=64,
        help_text="Página de Facebook a la que pertenece el token (la misma en Instagram vinculado).",
    )
    token_cifrado = models.TextField(blank=True, default="", help_text="Token de página cifrado. Nunca se expone.")
    token_expira_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Null: el token de página no informa vencimiento.",
    )
    estado = models.CharField(
        max_length=20,
        choices=ConexionEstado.choices,
        default=ConexionEstado.ACTIVA,
        db_index=True,
    )
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "social_connections"
        ordering = ["red", "cuenta_nombre"]
        constraints = [
            models.UniqueConstraint(
                fields=["usuario", "red", "cuenta_id"],
                name="uniq_conexion_usuario_red_cuenta",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.red}:{self.cuenta_nombre} ({self.estado})"


class PublicacionEstado(models.TextChoices):
    ESPERANDO_APROBACION = "esperando_aprobacion", "Esperando aprobación"
    PUBLICANDO = "publicando", "Publicando"
    PUBLICADO = "publicado", "Publicado"
    FALLIDO = "fallido", "Fallido"
    CANCELADO = "cancelado", "Cancelado"


class Publication(models.Model):
    """Publicación de una campaña en una cuenta conectada."""

    campaign = models.ForeignKey(Campaign, on_delete=models.CASCADE, related_name="publicaciones")
    conexion = models.ForeignKey(
        SocialConnection,
        on_delete=models.SET_NULL,
        null=True,
        related_name="publicaciones",
    )
    red = models.CharField(max_length=20, choices=RedSocial.choices)
    cuenta_nombre = models.CharField(max_length=150, help_text="Copia para mostrar aunque la cuenta se desconecte.")
    estado = models.CharField(
        max_length=30,
        choices=PublicacionEstado.choices,
        default=PublicacionEstado.ESPERANDO_APROBACION,
        db_index=True,
    )

    # ── Contenido congelado al aprobar ──
    copy_aprobado = models.TextField(blank=True, default="")
    imagen_aprobada_b64 = models.TextField(blank=True, null=True)
    version_aprobada = models.IntegerField(
        null=True,
        blank=True,
        help_text="Campaign.version que aprobó el cliente.",
    )

    # ── Resultado en Meta ──
    contenedor_id = models.CharField(max_length=64, blank=True, default="")
    externo_id = models.CharField(max_length=64, blank=True, default="")
    permalink = models.URLField(max_length=500, blank=True, default="")
    error = models.TextField(blank=True, default="")
    intentos = models.PositiveSmallIntegerField(default=0)

    solicitada_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="publicaciones_solicitadas",
    )
    publicado_at = models.DateTimeField(null=True, blank=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "social_publications"
        ordering = ["-fecha_creacion"]
        constraints = [
            models.UniqueConstraint(
                fields=["campaign", "conexion"],
                name="uniq_publicacion_campana_conexion",
            ),
        ]
        indexes = [
            models.Index(fields=["campaign", "estado"], name="idx_publicacion_campana_estado"),
        ]

    def __str__(self) -> str:
        return f"Publicación {self.pk} {self.red}:{self.cuenta_nombre} [{self.estado}]"


class PublicationMetric(models.Model):
    """
    Foto de las métricas de una publicación en un momento dado.

    Un valor que Meta no entrega (cuenta nueva, métrica no disponible o aún
    sin procesar: puede tardar hasta 48 h) se guarda como null, nunca como 0.
    """

    publicacion = models.ForeignKey(Publication, on_delete=models.CASCADE, related_name="metricas")
    me_gusta = models.IntegerField(null=True, blank=True, help_text="Likes en Instagram; reacciones en Facebook.")
    comentarios = models.IntegerField(null=True, blank=True)
    compartidos = models.IntegerField(null=True, blank=True)
    guardados = models.IntegerField(null=True, blank=True, help_text="Solo Instagram.")
    alcance = models.IntegerField(null=True, blank=True, help_text="Cuentas únicas que vieron la publicación.")
    vistas = models.IntegerField(null=True, blank=True)
    interacciones = models.IntegerField(null=True, blank=True, help_text="Total de interacciones (o clics en Facebook).")
    crudo = models.JSONField(default=dict, blank=True, help_text="Respuesta de Meta, para auditar.")
    error = models.TextField(blank=True, default="")
    obtenida_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "social_publication_metrics"
        ordering = ["-obtenida_at"]
        indexes = [
            models.Index(fields=["publicacion", "-obtenida_at"], name="idx_metrica_pub_fecha"),
        ]

    def __str__(self) -> str:
        return f"Métricas de publicación {self.publicacion_id} @ {self.obtenida_at:%Y-%m-%d %H:%M}"
