"""Fixtures de los callbacks de n8n (secreto compartido en cabecera)."""

import pytest
from django.conf import settings
from rest_framework.test import APIClient


@pytest.fixture
def n8n_client() -> APIClient:
    """Cliente que llama como n8n: con X-NexoMark-Token = N8N_WEBHOOK_TOKEN."""
    client = APIClient()
    client.credentials(HTTP_X_NEXOMARK_TOKEN=settings.N8N_WEBHOOK_TOKEN)
    return client
