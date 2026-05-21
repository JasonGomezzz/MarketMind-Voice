"""
MarketMind IA — Campaign Permissions
Permiso especial para el callback de n8n: valida el n8n_callback_token
del modelo Campaign en lugar de un JWT. No requiere usuario autenticado.
"""

from rest_framework.permissions import BasePermission

from .models import Campaign


class N8nCallbackPermission(BasePermission):
    """
    Autenticación sin JWT para el endpoint de callback de n8n.

    Valida que el campo 'n8n_callback_token' del body corresponda a una
    campaña existente en base de datos. Solo n8n conoce este UUID ya que
    Django lo incluye en el payload del webhook outgoing y nunca lo
    expone al frontend.

    Uso: authentication_classes = [], permission_classes = [N8nCallbackPermission]
    """

    message = "Token de callback inválido o ausente."

    def has_permission(self, request, view) -> bool:
        token = request.data.get("n8n_callback_token")
        if not token:
            return False
        try:
            return Campaign.objects.filter(n8n_callback_token=token).exists()
        except Exception:
            return False
