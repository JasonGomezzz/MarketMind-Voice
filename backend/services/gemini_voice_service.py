"""Generacion de voz para la aplicacion movil usando Gemini TTS."""

import base64
import io
import wave

import requests
from django.conf import settings


class GeminiVoiceError(RuntimeError):
    """Error seguro para exponer al cliente movil."""


def _pcm_to_wav(pcm: bytes, sample_rate: int = 24000) -> bytes:
    """Empaqueta PCM mono de 16 bits entregado por Gemini como WAV reproducible."""
    output = io.BytesIO()
    with wave.open(output, "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(sample_rate)
        wav.writeframes(pcm)
    return output.getvalue()


def synthesize_speech(text: str) -> bytes:
    api_key = settings.GEMINI_API_KEY.strip()
    if not api_key or api_key.startswith("tu-") or "tu-api-key" in api_key:
        raise GeminiVoiceError("La voz Gemini aun no tiene una API key valida.")

    url = (
        "https://generativelanguage.googleapis.com/v1beta/models/"
        f"{settings.GEMINI_TTS_MODEL}:generateContent"
    )
    payload = {
        "contents": [{"parts": [{"text": (
            "Lee el siguiente contenido en espanol latino, con una voz clara, "
            "profesional y cercana, adecuada para presentar una campana publicitaria. "
            f"Contenido: {text}"
        )}]}],
        "generationConfig": {
            "responseModalities": ["AUDIO"],
            "speechConfig": {
                "voiceConfig": {
                    "prebuiltVoiceConfig": {"voiceName": settings.GEMINI_TTS_VOICE}
                }
            },
        },
    }

    try:
        response = requests.post(url, params={"key": api_key}, json=payload, timeout=30)
        response.raise_for_status()
        data = response.json()
        inline = data["candidates"][0]["content"]["parts"][0]["inlineData"]
        audio = base64.b64decode(inline["data"])
        mime_type = inline.get("mimeType", "")
        sample_rate = 24000
        if "rate=" in mime_type:
            sample_rate = int(mime_type.split("rate=", 1)[1].split(";", 1)[0])
        if audio[:4] == b"RIFF":
            return audio
        return _pcm_to_wav(audio, sample_rate)
    except (requests.RequestException, KeyError, ValueError, TypeError) as exc:
        raise GeminiVoiceError("Gemini no pudo generar la voz en este momento.") from exc
