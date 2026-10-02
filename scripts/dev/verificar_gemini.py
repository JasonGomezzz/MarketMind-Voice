"""Verifica la clave de Gemini y los modelos que usa MarketMind.

Lee GEMINI_API_KEY del entorno o de backend/.env. Nunca imprime la clave.

Desde la raíz del repo, con el venv del backend:

    backend/venv/bin/python scripts/dev/verificar_gemini.py
        Lista los modelos disponibles para la clave. No consume cuota.

    backend/venv/bin/python scripts/dev/verificar_gemini.py --interpretar
        Una llamada real de texto: interpreta un brief con services.intent_service.

    backend/venv/bin/python scripts/dev/verificar_gemini.py --imagen gemini-3.1-flash-image
        Una llamada real de imagen con el mismo cuerpo que envía el workflow de n8n.
        Guarda el resultado en ci-artifacts/ (ignorado por Git).
"""

import argparse
import base64
import os
import sys
import time
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parents[2]
API = "https://generativelanguage.googleapis.com/v1beta"
BRIEF = (
    "Quiero una campaña para una cafetería en Instagram con tono casual, "
    "promocionando un 2x1 en capuchinos para universitarios los viernes"
)
PROMPT_IMAGEN = (
    "Professional advertising photo for a coffee shop: two warm cappuccinos on a "
    "wooden table, soft morning light, photorealistic, no text overlay."
)


def leer_clave() -> str:
    clave = os.environ.get("GEMINI_API_KEY", "").strip()
    if not clave:
        env = ROOT / "backend" / ".env"
        if env.exists():
            for linea in env.read_text().splitlines():
                if linea.startswith("GEMINI_API_KEY="):
                    clave = linea.split("=", 1)[1].strip().strip('"').strip("'")
    if not clave:
        sys.exit("Falta GEMINI_API_KEY en backend/.env (no la pegues en el chat).")
    return clave


def listar_modelos(clave: str) -> None:
    response = httpx.get(f"{API}/models", params={"key": clave, "pageSize": 1000}, timeout=20)
    if response.status_code != 200:
        sys.exit(f"La clave no pudo listar modelos: HTTP {response.status_code}.")
    nombres = sorted(m["name"].removeprefix("models/") for m in response.json().get("models", []))
    print(f"Modelos visibles para la clave: {len(nombres)}")
    for buscado in ("gemini-2.5-flash", "gemini-2.5-flash-image"):
        print(f"  {buscado}: {'disponible' if buscado in nombres else 'NO disponible'}")
    imagen = [n for n in nombres if "image" in n and "gemini" in n]
    print("  Modelos Gemini de imagen:", ", ".join(imagen) or "ninguno")


def interpretar() -> None:
    os.environ["USE_MOCK_AI"] = "False"
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings.dev")
    sys.path.insert(0, str(ROOT / "backend"))
    os.chdir(ROOT / "backend")
    import django

    django.setup()
    from services.intent_service import IntentInterpretationError, interpretar_brief

    try:
        resultado = interpretar_brief(BRIEF)
    except IntentInterpretationError as exc:
        sys.exit(f"Interpretación real falló: {exc}")
    print(f"Interpretación real con {resultado.modelo} en {resultado.duracion_ms} ms")
    for campo, valor in resultado.campos.items():
        print(f"  {campo}: {valor!r}")
    print("  advertencias:", resultado.advertencias or "ninguna")
    print("  uso reportado:", resultado.uso if resultado.uso is not None else "no reportado (null)")


def generar_imagen(clave: str, modelo: str) -> None:
    inicio = time.monotonic()
    response = httpx.post(
        f"{API}/models/{modelo}:generateContent",
        params={"key": clave},
        json={"contents": [{"parts": [{"text": PROMPT_IMAGEN}]}]},
        timeout=90,
    )
    segundos = time.monotonic() - inicio
    if response.status_code != 200:
        sys.exit(f"{modelo}: HTTP {response.status_code} en {segundos:.1f} s. {response.text[:300]}")
    data = response.json()
    partes = data.get("candidates", [{}])[0].get("content", {}).get("parts", [])
    imagen = next((p["inlineData"] for p in partes if p.get("inlineData", {}).get("data")), None)
    if not imagen:
        sys.exit(f"{modelo}: respondió sin imagen (el workflow pondría el placeholder).")
    destino = ROOT / "ci-artifacts" / f"gemini-prueba-{modelo}.{imagen.get('mimeType', 'image/png').split('/')[-1]}"
    destino.parent.mkdir(exist_ok=True)
    destino.write_bytes(base64.b64decode(imagen["data"]))
    print(f"{modelo}: imagen {imagen.get('mimeType')} de {destino.stat().st_size // 1024} KB en {segundos:.1f} s")
    print(f"  guardada en {destino.relative_to(ROOT)}")
    print("  uso reportado:", data.get("usageMetadata") or "no reportado (null)")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--interpretar", action="store_true", help="una llamada real de texto")
    parser.add_argument("--imagen", metavar="MODELO", help="una llamada real de imagen con ese modelo")
    args = parser.parse_args()

    clave = leer_clave()
    listar_modelos(clave)
    if args.interpretar:
        interpretar()
    if args.imagen:
        generar_imagen(clave, args.imagen)


if __name__ == "__main__":
    main()
