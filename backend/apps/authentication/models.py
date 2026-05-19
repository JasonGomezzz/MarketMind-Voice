"""
MarketMind IA — Authentication Models
Define el modelo User customizado con roles superadmin/marketero/cliente.
Criterios HU1: registro con roles, email único, password bcrypt.
"""

from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.utils import timezone


class UserRole(models.TextChoices):
    """Roles disponibles en el sistema MarketMind IA."""
    SUPERADMIN = "superadmin", "Super Administrador"
    MARKETERO = "marketero", "Marketero"
    CLIENTE = "cliente", "Cliente"


class UserManager(BaseUserManager):
    """Manager customizado para el modelo User."""

    def create_user(
        self,
        email: str,
        password: str,
        nombre: str,
        rol: str = UserRole.CLIENTE,
        **extra_fields,
    ) -> "User":
        """
        Crea y guarda un usuario con email y contraseña.

        Args:
            email: Email único del usuario.
            password: Contraseña en texto plano (se encripta con bcrypt).
            nombre: Nombre completo del usuario.
            rol: Rol dentro del sistema (superadmin/marketero/cliente).
            **extra_fields: Campos adicionales opcionales.

        Returns:
            Instancia del usuario creado.

        Raises:
            ValueError: Si el email no es proporcionado.
        """
        if not email:
            raise ValueError("El campo email es obligatorio.")

        email = self.normalize_email(email)

        if rol not in UserRole.values:
            raise ValueError(
                f"Rol inválido '{rol}'. Valores válidos: {UserRole.values}"
            )

        user: "User" = self.model(
            email=email,
            nombre=nombre,
            rol=rol,
            **extra_fields,
        )
        user.set_password(password)  # Django usa bcrypt si está configurado
        user.save(using=self._db)
        return user

    def create_superuser(
        self,
        email: str,
        password: str,
        nombre: str = "Super Admin",
        **extra_fields,
    ) -> "User":
        """
        Crea un superusuario con acceso completo al admin de Django.

        Args:
            email: Email del superusuario.
            password: Contraseña en texto plano.
            nombre: Nombre del superusuario.
            **extra_fields: Campos adicionales.

        Returns:
            Instancia del superusuario creado.
        """
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)

        if not extra_fields.get("is_staff"):
            raise ValueError("Superusuario debe tener is_staff=True.")
        if not extra_fields.get("is_superuser"):
            raise ValueError("Superusuario debe tener is_superuser=True.")

        return self.create_user(
            email=email,
            password=password,
            nombre=nombre,
            rol=UserRole.SUPERADMIN,
            **extra_fields,
        )


class User(AbstractBaseUser, PermissionsMixin):
    """
    Modelo de usuario customizado para MarketMind IA.

    Extiende AbstractBaseUser para control total sobre autenticación.
    Usa email como campo de identificación principal (no username).

    Roles:
        - superadmin: Acceso total al sistema y panel admin.
        - marketero: Crea y gestiona campañas publicitarias.
        - cliente: Aprueba o rechaza propuestas de campaña.

    Campos de auditoría:
        - fecha_creacion: Timestamp de registro.
        - fecha_actualizacion: Último update del registro.
        - ultimo_login: Gestionado por AbstractBaseUser.
    """

    # ── Identificación ──────────────────────────────────────
    email = models.EmailField(
        unique=True,
        max_length=255,
        verbose_name="Email",
        help_text="Email único del usuario. Usado como campo de login.",
    )
    nombre = models.CharField(
        max_length=150,
        verbose_name="Nombre completo",
    )

    # ── Rol ─────────────────────────────────────────────────
    rol = models.CharField(
        max_length=20,
        choices=UserRole.choices,
        default=UserRole.CLIENTE,
        verbose_name="Rol",
        help_text="Define los permisos del usuario en el sistema.",
    )

    # ── Estado ──────────────────────────────────────────────
    is_active = models.BooleanField(
        default=True,
        verbose_name="Activo",
        help_text="Desactiva para suspender sin eliminar la cuenta.",
    )
    is_staff = models.BooleanField(
        default=False,
        verbose_name="Staff",
        help_text="Acceso al admin de Django.",
    )

    # ── Plan de suscripción ──────────────────────────────────
    tokens_disponibles = models.IntegerField(
        default=100,
        verbose_name="Tokens disponibles",
        help_text="Cuota de generaciones IA restantes en el plan actual.",
    )

    # ── Token version (para invalidar JWTs al suspender — HU18) ──
    token_version = models.IntegerField(
        default=0,
        verbose_name="Versión de token",
        help_text="Incrementar invalida todos los JWT emitidos anteriormente.",
    )

    # ── Auditoría ────────────────────────────────────────────
    fecha_creacion = models.DateTimeField(
        default=timezone.now,
        verbose_name="Fecha de registro",
    )
    fecha_actualizacion = models.DateTimeField(
        auto_now=True,
        verbose_name="Última actualización",
    )

    # ── Manager ─────────────────────────────────────────────
    objects = UserManager()

    # ── AbstractBaseUser config ──────────────────────────────
    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["nombre"]  # Pedido por createsuperuser además de email/password

    class Meta:
        verbose_name = "Usuario"
        verbose_name_plural = "Usuarios"
        db_table = "users"
        ordering = ["-fecha_creacion"]
        indexes = [
            models.Index(fields=["email"], name="idx_user_email"),
            models.Index(fields=["rol"], name="idx_user_rol"),
        ]

    def __str__(self) -> str:
        return f"{self.nombre} <{self.email}> [{self.rol}]"

    # ── Helpers de rol ───────────────────────────────────────
    @property
    def is_superadmin(self) -> bool:
        """Verifica si el usuario tiene rol superadmin."""
        return self.rol == UserRole.SUPERADMIN

    @property
    def is_marketero(self) -> bool:
        """Verifica si el usuario tiene rol marketero."""
        return self.rol == UserRole.MARKETERO

    @property
    def is_cliente(self) -> bool:
        """Verifica si el usuario tiene rol cliente."""
        return self.rol == UserRole.CLIENTE
