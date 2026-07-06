"""
MarketMind IA — Servicio de mejora de copy con Gemini (síncrono).

A diferencia del flujo de generación completa (que pasa por n8n para copy +
imagen), este servicio llama a Gemini DIRECTAMENTE para reescribir/mejorar el
texto ya generado, SIN tocar la imagen. Se usa en el botón "Mejorar redacción
con IA" del editor: es una operación rápida (solo texto) y síncrona, por lo que
no necesita la orquestación asíncrona de n8n.

En modo USE_MOCK_AI=True devuelve una mejora simulada (no consume cuota Gemini).
"""

import logging

import httpx
from django.conf import settings

logger = logging.getLogger(__name__)

_GEMINI_URL = (
    "https://generativelanguage.googleapis.com/v1beta/models/"
    "{model}:generateContent"
)


def improve_copy(texto_actual: str, industria: str, tono: str, plataforma: str) -> str:
    """
    Mejora el copy publicitario dado usando Gemini (o un mock en dev).

    Args:
        texto_actual: El copy actual a mejorar.
        industria/tono/plataforma: Contexto de la campaña para guiar el estilo.

    Returns:
        El copy mejorado. Si Gemini falla, devuelve el texto original (nunca
        rompe el flujo del editor).
    """
    texto_actual = (texto_actual or "").strip()
    if not texto_actual:
        return texto_actual

    if settings.USE_MOCK_AI:
        logger.info("USE_MOCK_AI activo — mejora de copy simulada.")
        return (
            f"✨ {texto_actual} "
            "¡No dejes pasar esta oportunidad — actúa hoy!"
        )

    prompt = (
        "Eres un copywriter publicitario senior. Mejora el siguiente copy para "
        f"una campaña de industria '{industria}', tono '{tono}', plataforma "
        f"'{plataforma}'. Hazlo más persuasivo, claro y con mejor gancho, "
        "manteniendo el idioma español y una longitud similar. Conserva los "
        "hashtags y emojis si aportan. Responde SOLO con el copy mejorado, sin "
        "comillas ni explicaciones.\n\nCOPY ACTUAL:\n" + texto_actual
    )

    body = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "thinkingConfig": {"thinkingBudget": 0},
            "maxOutputTokens": 1024,
        },
    }
    url = _GEMINI_URL.format(model=settings.GEMINI_MODEL)

    try:
        response = httpx.post(
            url,
            params={"key": settings.GEMINI_API_KEY},
            json=body,
            timeout=30.0,
        )
        response.raise_for_status()
        data = response.json()
        # Gemini 2.5 puede devolver thought parts antes del texto real.
        parts = data["candidates"][0]["content"]["parts"]
        texto = next(
            (p["text"] for p in parts if p.get("text", "").strip()),
            "",
        ).strip()
        return texto or texto_actual
    except (httpx.HTTPError, KeyError, IndexError) as exc:
        logger.warning("Gemini no pudo mejorar el copy: %s", exc)
        return texto_actual
