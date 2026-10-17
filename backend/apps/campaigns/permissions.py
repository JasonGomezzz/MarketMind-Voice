"""
MarketMind IA — Campaign Permissions
Permiso especial para los callbacks de n8n: secreto compartido en cabecera más
el n8n_callback_token de la campaña, en lugar de un JWT.
"""

from rest_framework.permissions import BasePermission

from services.n8n_service import N8N_TOKEN_HEADER, secreto_n8n_valido

from .models import Campaign


class N8nCallbackPermission(BasePermission):
    """
    Autenticación sin JWT para los callbacks de n8n. Exige las dos cosas:

    1. El secreto compartido N8N_WEBHOOK_TOKEN en el encabezado X-NexoMark-Token
       (comparación en tiempo constante; un secreto vacío nunca autentica).
    2. Un 'n8n_callback_token' en el body que corresponda a una campaña. Django
       lo rota en cada intento de generación, así que solo vale el del último
       intento: un callback viejo no encuentra campaña y se rechaza.

    Uso: authentication_classes = [], permission_classes = [N8nCallbackPermission]
    """

    message = "Callback de n8n no autorizado."

    def has_permission(self, request, view) -> bool:
        if not secreto_n8n_valido(request.headers.get(N8N_TOKEN_HEADER)):
            return False
        token = request.data.get("n8n_callback_token")
        if not token:
            return False
        try:
            return Campaign.objects.filter(n8n_callback_token=token).exists()
        except Exception:
            # Un valor que no es UUID no autentica (y no debe dar 500).
            return False
