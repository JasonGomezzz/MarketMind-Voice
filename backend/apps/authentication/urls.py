"""
MarketMind IA — Authentication URLs
Monta los endpoints de auth bajo el prefijo /api/auth/
"""

from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from .views import LogoutView, RegisterView
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
]
