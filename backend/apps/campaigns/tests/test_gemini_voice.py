"""Pruebas del puente seguro entre Flutter y Gemini TTS."""

from unittest.mock import patch

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings
from rest_framework.test import APIClient

from services.gemini_transcription_service import GeminiTranscriptionError


VOICE_URL = "/api/campaigns/voice/synthesize/"
TRANSCRIPTION_URL = "/api/campaigns/voice/transcribe/"


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


@pytest.mark.django_db
class TestGeminiTranscriptionView:
    def test_requires_authentication(self):
        audio = SimpleUploadedFile("voice.webm", b"audio", content_type="audio/webm")
        response = APIClient().post(TRANSCRIPTION_URL, {"audio": audio}, format="multipart")
        assert response.status_code == 401

    def test_requires_audio_file(self, api_client):
        response = api_client.post(TRANSCRIPTION_URL, {}, format="multipart")
        assert response.status_code == 400

    def test_rejects_unsupported_format(self, api_client):
        audio = SimpleUploadedFile("voice.txt", b"audio", content_type="text/plain")
        response = api_client.post(TRANSCRIPTION_URL, {"audio": audio}, format="multipart")
        assert response.status_code == 400

    def test_returns_gemini_transcript(self, api_client):
        audio = SimpleUploadedFile("voice.webm", b"audio", content_type="audio/webm")
        with patch(
            "apps.campaigns.views.transcribe_speech",
            return_value="Campaña para emprendedores peruanos.",
        ):
            response = api_client.post(
                TRANSCRIPTION_URL,
                {"audio": audio},
                format="multipart",
            )
        assert response.status_code == 200
        assert response.data == {
            "transcript": "Campaña para emprendedores peruanos.",
            "provider": "gemini",
        }

    def test_reports_gemini_failure(self, api_client):
        audio = SimpleUploadedFile("voice.webm", b"audio", content_type="audio/webm")
        with patch(
            "apps.campaigns.views.transcribe_speech",
            side_effect=GeminiTranscriptionError("Gemini no detectó voz en el audio."),
        ):
            response = api_client.post(
                TRANSCRIPTION_URL,
                {"audio": audio},
                format="multipart",
            )
        assert response.status_code == 503
