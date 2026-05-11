"""
MarketMind IA — Custom Token View
Extiende TokenObtainPairView para aplicar rate limiting en login.
"""

from rest_framework_simplejwt.views import TokenObtainPairView

from .serializers import CustomTokenObtainPairSerializer
from .throttles import AuthRateThrottle


class CustomTokenObtainPairView(TokenObtainPairView):
    """
    Vista de login con JWT customizado.
    - Usa CustomTokenObtainPairSerializer para incluir 'role' en el payload.
    - Aplica AuthRateThrottle (10 intentos/minuto) para prevenir brute-force.
    """

    serializer_class = CustomTokenObtainPairSerializer
    throttle_classes = [AuthRateThrottle]
