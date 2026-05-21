"""
MarketMind IA — Authentication Throttles
Rate limiting granular para registro y login.

DRF parse_rate() solo acepta s/m/h/d como período único.
Sobrescribimos parse_rate() para expresar ventanas de N minutos exactos.
"""

from rest_framework.throttling import AnonRateThrottle


class RegisterRateThrottle(AnonRateThrottle):
    """5 intentos de registro por 10 minutos por IP."""

    scope = "register"

    def parse_rate(self, rate: str) -> tuple[int, int]:
        return (5, 600)  # 5 requests / 600 segundos (10 min)


class LoginRateThrottle(AnonRateThrottle):
    """10 intentos de login por 5 minutos por IP."""

    scope = "login"

    def parse_rate(self, rate: str) -> tuple[int, int]:
        return (10, 300)  # 10 requests / 300 segundos (5 min)
