"""
MarketMind IA — Custom Token View
Extiende TokenObtainPairView para aplicar rate limiting en login.
"""

from rest_framework_simplejwt.views import TokenObtainPairView

from .serializers import CustomTokenObtainPairSerializer
from .throttles import LoginRateThrottle


class CustomTokenObtainPairView(TokenObtainPairView):
    """
    Vista de login con JWT customizado.
    - Usa CustomTokenObtainPairSerializer para incluir 'role' en el payload.
    - Aplica LoginRateThrottle (10 intentos / 5 min) para prevenir brute-force.
    """

    serializer_class = CustomTokenObtainPairSerializer
    throttle_classes = [LoginRateThrottle]
