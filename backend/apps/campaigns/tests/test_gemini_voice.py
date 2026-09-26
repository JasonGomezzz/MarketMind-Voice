"""Pruebas del puente seguro entre Flutter y Gemini TTS."""

from unittest.mock import patch

import pytest
from django.test import override_settings
from rest_framework.test import APIClient


VOICE_URL = "/api/campaigns/voice/synthesize/"


@pytest.mark.django_db
class TestGeminiVoiceView:
    def test_requires_authentication(self):
        response = APIClient().post(VOICE_URL, {"text": "Hola"}, format="json")
        assert response.status_code == 401

    def test_rejects_empty_text(self, api_client):
        response = api_client.post(VOICE_URL, {"text": ""}, format="json")
        assert response.status_code == 400

    @override_settings(GEMINI_API_KEY="")
    def test_reports_device_fallback_without_key(self, api_client):
        response = api_client.post(VOICE_URL, {"text": "Campaña demo"}, format="json")
        assert response.status_code == 503
        assert response.data["fallback"] == "device_tts"

    def test_returns_wav_generated_by_service(self, api_client):
        with patch("apps.campaigns.views.synthesize_speech", return_value=b"RIFF-demo"):
            response = api_client.post(VOICE_URL, {"text": "Campaña demo"}, format="json")
        assert response.status_code == 200
        assert response["Content-Type"] == "audio/wav"
        assert response.content == b"RIFF-demo"
