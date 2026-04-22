"""
Vision fallback — screenshot + Gemma 4 multimodal.

Se usa cuando:
- La Accessibility API no está disponible o no tiene datos
- El usuario pide "describí lo que hay en pantalla"
- La app activa no implementa bien la Accessibility API (Electron, juegos, etc.)

Requiere:
- Pillow (pip install Pillow) — para tomar el screenshot
- Un modelo multimodal en Ollama (gemma4, llava, moondream, etc.)
"""
from __future__ import annotations

import io
import logging

logger = logging.getLogger(__name__)


async def describe_screen(adapter, prompt: str = "") -> str:
    """
    Toma un screenshot de la pantalla completa y lo describe con Gemma 4 Vision.

    Args:
        adapter: instancia de OllamaAdapter con modelo multimodal
        prompt: instrucción adicional. Vacío = descripción general de accesibilidad.

    Returns:
        Descripción oral de la pantalla, lista para TTS.
    """
    try:
        screenshot_bytes = _take_screenshot()
        return await adapter.vision_describe(screenshot_bytes, prompt)
    except Exception as e:
        logger.error(f"vision_fallback.describe_screen error: {e}")
        return "Señor, no pude capturar la pantalla."


def _take_screenshot() -> bytes:
    """Captura la pantalla completa y devuelve los bytes PNG."""
    try:
        import PIL.ImageGrab
        img = PIL.ImageGrab.grab()
    except Exception:
        # Fallback con pyautogui en caso de que ImageGrab falle (Linux, etc.)
        import pyautogui
        import PIL.Image
        img = pyautogui.screenshot()

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()
