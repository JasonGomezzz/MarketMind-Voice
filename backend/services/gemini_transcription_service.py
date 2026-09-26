"""Transcripción de audio con Gemini sin exponer credenciales al cliente."""

import base64

import requests
from django.conf import settings


class GeminiTranscriptionError(RuntimeError):
    """Error seguro que puede devolverse a web y Flutter."""


def transcribe_speech(audio: bytes, mime_type: str) -> str:
    """Envía audio a Gemini y devuelve una transcripción limpia en español."""
    api_key = settings.GEMINI_API_KEY.strip()
    if not api_key or api_key.startswith("tu-") or "tu-api-key" in api_key:
        raise GeminiTranscriptionError("La transcripción Gemini no tiene una API key válida.")

    url = (
        "https://generativelanguage.googleapis.com/v1beta/models/"
        f"{settings.GEMINI_TRANSCRIPTION_MODEL}:generateContent"
    )
    payload = {
        "contents": [
            {
                "parts": [
                    {
                        "text": (
                            "Transcribe fielmente este audio en español. Devuelve únicamente "
                            "el texto pronunciado, sin explicaciones, etiquetas ni comillas. "
                            "Conserva nombres propios, puntuación y terminología de marketing."
                        )
                    },
                    {
                        "inlineData": {
                            "mimeType": mime_type,
                            "data": base64.b64encode(audio).decode("ascii"),
                        }
                    },
                ]
            }
        ],
        "generationConfig": {"temperature": 0.0},
    }

    try:
        response = requests.post(
            url,
            params={"key": api_key},
            json=payload,
            timeout=settings.GEMINI_TRANSCRIPTION_TIMEOUT,
        )
        response.raise_for_status()
        parts = response.json()["candidates"][0]["content"]["parts"]
        transcript = "".join(part.get("text", "") for part in parts).strip()
        if not transcript:
            raise GeminiTranscriptionError("Gemini no detectó voz en el audio.")
        return transcript
    except GeminiTranscriptionError:
        raise
    except (requests.RequestException, KeyError, IndexError, TypeError, ValueError) as exc:
        raise GeminiTranscriptionError(
            "Gemini no pudo transcribir el audio en este momento."
        ) from exc
