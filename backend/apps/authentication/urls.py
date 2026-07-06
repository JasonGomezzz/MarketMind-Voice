"""
MarketMind IA — Authentication URLs
Monta los endpoints de auth bajo el prefijo /api/auth/
"""

from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from .views import AuthBrandContentView, ChangePasswordView, LogoutView, MeView, RegisterView
from .token_views import CustomTokenObtainPairView

urlpatterns = [
    # HU1: Registro de usuarios
    path("register/", RegisterView.as_view(), name="auth-register"),

    # HU2: Login → access_token + refresh_token + role
    path("token/", CustomTokenObtainPairView.as_view(), name="auth-token"),

    # HU2: Refresh del access token
    path("token/refresh/", TokenRefreshView.as_view(), name="auth-token-refresh"),

    # Logout con blacklist del refresh token
    path("logout/", LogoutView.as_view(), name="auth-logout"),

    # HU8: datos del usuario autenticado en tiempo real (tokens_disponibles)
    # GET = perfil · PATCH = editar nombre (Settings)
    path("me/", MeView.as_view(), name="auth-me"),

    # Settings: cambio de contraseña del propio usuario
    path("me/change-password/", ChangePasswordView.as_view(), name="auth-change-password"),

    # Contenido público para panel Login/Register
    path("brand-content/", AuthBrandContentView.as_view(), name="auth-brand-content"),
]
