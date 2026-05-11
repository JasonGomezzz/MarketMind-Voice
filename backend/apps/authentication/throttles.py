"""
MarketMind IA — Authentication Throttles
Rate limiting específico para endpoints de registro y login.
10 intentos por minuto por IP (anónimo) según configuración base.
"""

from rest_framework.throttling import AnonRateThrottle


class AuthRateThrottle(AnonRateThrottle):
    """
    Throttle específico para endpoints de autenticación.
    Aplica el rate 'auth' definido en DEFAULT_THROTTLE_RATES: 10/minute.
    Usado en RegisterView y sobreescribible en TokenObtainPairView.
    """

    scope = "auth"
