"""
MarketMind IA — Campaign Model
Modelo central del sistema: representa una campaña publicitaria
con máquina de estados finitos (FSM) para controlar el ciclo de vida.
"""

import uuid
from typing import ClassVar

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone


class CampaignTono(models.TextChoices):
    """Tonos disponibles para el copy generado por IA."""
    PROFESIONAL = "profesional", "Profesional"
    CASUAL = "casual", "Casual"
    URGENTE = "urgente", "Urgente"
    INSPIRACIONAL = "inspiracional", "Inspiracional"
    HUMORISTICO = "humoristico", "Humorístico"
    PERSUASIVO = "persuasivo", "Persuasivo"


class CampaignPlataforma(models.TextChoices):
    """Plataformas de publicación soportadas."""
    INSTAGRAM = "instagram", "Instagram"
    FACEBOOK = "facebook", "Facebook"
    TWITTER = "twitter", "Twitter / X"
    LINKEDIN = "linkedin", "LinkedIn"
    GOOGLE_ADS = "google_ads", "Google Ads"
    TIKTOK = "tiktok", "TikTok"


class CampaignStatus(models.TextChoices):
    """
    Estados del ciclo de vida de una campaña.

    Flujo principal:
        BORRADOR → PENDIENTE_IA → GENERADO → PENDIENTE_APROBACION
                                                  ↓             ↓
                                               APROBADO     RECHAZADO
                                                              ↓
                                                           BORRADOR (reintento)
    """
    BORRADOR = "borrador", "Borrador"
    PENDIENTE_IA = "pendiente_ia", "Pendiente IA"
    GENERADO = "generado", "Generado"
    PENDIENTE_APROBACION = "pendiente_aprobacion", "Pendiente Aprobación"
    APROBADO = "aprobado", "Aprobado"
    RECHAZADO = "rechazado", "Rechazado"


class Campaign(models.Model):
    """
    Campaña publicitaria generada con asistencia de IA.

    Ciclo de vida controlado por FSM. Solo se permiten transiciones
    definidas en VALID_TRANSITIONS; cualquier otra lanza InvalidTransitionError.

    Relaciones:
        - marketero: Usuario con rol 'marketero' que creó la campaña.
          FK a settings.AUTH_USER_MODEL para no acoplar al modelo User directamente.

    Campos de IA:
        - prompt: Texto de entrada enviado a Gemini vía n8n.
        - texto_generado: Copy publicitario devuelto por Gemini.
        - imagen_url: URL de imagen generada por Stability AI (HU21, Sprint 4).
    """

    VALID_TRANSITIONS: ClassVar[dict[str, list[str]]] = {
        CampaignStatus.BORRADOR: [CampaignStatus.PENDIENTE_IA],
        CampaignStatus.PENDIENTE_IA: [CampaignStatus.GENERADO, CampaignStatus.BORRADOR],
        CampaignStatus.GENERADO: [CampaignStatus.PENDIENTE_APROBACION],
        CampaignStatus.PENDIENTE_APROBACION: [
            CampaignStatus.APROBADO,
            CampaignStatus.RECHAZADO,
        ],
        CampaignStatus.APROBADO: [],
        CampaignStatus.RECHAZADO: [CampaignStatus.BORRADOR],
    }

    # ── Identificación ──────────────────────────────────────
    titulo = models.CharField(
        max_length=200,
        verbose_name="Título de la campaña",
    )
    cliente_nombre = models.CharField(
        max_length=150,
        verbose_name="Nombre del cliente",
    )
    industria = models.CharField(
        max_length=100,
        verbose_name="Industria",
        help_text="Ej: tecnología, retail, salud, educación.",
    )

    # ── Configuración IA ────────────────────────────────────
    tono = models.CharField(
        max_length=20,
        choices=CampaignTono.choices,
        default=CampaignTono.PROFESIONAL,
        verbose_name="Tono del mensaje",
    )
    plataforma = models.CharField(
        max_length=20,
        choices=CampaignPlataforma.choices,
        default=CampaignPlataforma.INSTAGRAM,
        verbose_name="Plataforma de publicación",
    )
    prompt = models.TextField(
        verbose_name="Prompt de entrada",
        help_text="Descripción de la campaña enviada a Gemini vía n8n.",
    )

    # ── Resultado IA ────────────────────────────────────────
    texto_generado = models.TextField(
        blank=True,
        default="",
        verbose_name="Copy generado",
        help_text="Texto publicitario devuelto por Gemini.",
    )
    imagen_url = models.URLField(
        blank=True,
        null=True,
        verbose_name="URL de imagen",
        help_text="Imagen generada por Stability AI (HU21, Sprint 4).",
    )

    # ── Auditoría IA ────────────────────────────────────────
    n8n_callback_token = models.UUIDField(
        default=uuid.uuid4,
        unique=True,
        editable=False,
        verbose_name="Token callback n8n",
        help_text="UUID para autenticar el callback de n8n. No exponer al frontend.",
    )
    tokens_consumidos = models.IntegerField(
        default=0,
        verbose_name="Tokens consumidos",
    )
    intentos_generacion = models.IntegerField(
        default=0,
        verbose_name="Intentos de generación",
        help_text="Máximo 3 intentos por campaña.",
    )
    ia_error_message = models.TextField(
        blank=True,
        null=True,
        verbose_name="Error IA",
        help_text="Último error devuelto por n8n/Gemini.",
    )

    # ── Optimistic locking — Spring Boot JPA usa @Version sobre este campo ──
    version = models.IntegerField(
        default=1,
        verbose_name="Versión",
    )

    # ── FSM ─────────────────────────────────────────────────
    estado = models.CharField(
        max_length=30,
        choices=CampaignStatus.choices,
        default=CampaignStatus.BORRADOR,
        verbose_name="Estado",
        db_index=True,
    )

    # ── Relaciones ──────────────────────────────────────────
    marketero = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="campaigns",
        verbose_name="Marketero",
        help_text="Usuario con rol marketero que creó y gestiona esta campaña.",
    )

    # ── Auditoría ────────────────────────────────────────────
    fecha_creacion = models.DateTimeField(
        default=timezone.now,
        verbose_name="Fecha de creación",
    )
    fecha_actualizacion = models.DateTimeField(
        auto_now=True,
        verbose_name="Última actualización",
    )

    class Meta:
        verbose_name = "Campaña"
        verbose_name_plural = "Campañas"
        db_table = "campaigns"
        ordering = ["-fecha_creacion"]
        indexes = [
            models.Index(fields=["estado"], name="idx_campaign_estado"),
            models.Index(fields=["marketero", "estado"], name="idx_campaign_marketero_estado"),
        ]

    def __str__(self) -> str:
        return f"{self.titulo} [{self.estado}] — {self.cliente_nombre}"

    def transition_to(self, nuevo_estado: str) -> None:
        """
        Cambia el estado de la campaña validando la transición contra VALID_TRANSITIONS.

        Solo permite transiciones explícitamente definidas en VALID_TRANSITIONS.
        Guarda el objeto en BD si la transición es válida.

        Args:
            nuevo_estado: Valor de CampaignStatus al que se quiere transicionar.

        Raises:
            ValidationError: Si la transición desde el estado actual no está permitida.
            ValidationError: Si nuevo_estado no es un valor válido de CampaignStatus.

        Example:
            >>> campaign.transition_to(CampaignStatus.PENDIENTE_IA)
        """
        if nuevo_estado not in CampaignStatus.values:
            raise ValidationError(
                f"Estado '{nuevo_estado}' no es válido. "
                f"Valores permitidos: {CampaignStatus.values}"
            )

        estados_permitidos = self.VALID_TRANSITIONS.get(self.estado, [])

        if nuevo_estado not in estados_permitidos:
            raise ValidationError(
                f"Transición inválida: '{self.estado}' → '{nuevo_estado}'. "
                f"Desde '{self.estado}' solo se permite: {estados_permitidos or ['ninguno (estado final)']}"
            )

        self.estado = nuevo_estado
        self.save(update_fields=["estado", "fecha_actualizacion"])
