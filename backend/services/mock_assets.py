"""Recursos gráficos usados cuando Gemini no devuelve una imagen."""

import base64
from pathlib import Path


_ASSET_PATH = (
    Path(__file__).resolve().parent
    / "assets"
    / "nexomark-image-unavailable.png"
)

MOCK_IMAGE_B64 = base64.b64encode(_ASSET_PATH.read_bytes()).decode("ascii")
