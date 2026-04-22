"""
ScreenReaderEngine — lector de pantalla universal para Jarvis.

Funciona igual que JAWS/NVDA: lee el árbol de accesibilidad del SO.
Sin adaptadores por app. Funciona con Excel, Word, Chrome, cualquier cosa.

Tres capas en cascada:
    1. Accessibility API nativa (pywinauto/pyobjc) — la correcta, sin OCR
    2. Gemma 4 Vision (screenshot) — fallback para apps sin Accessibility API
    3. pyautogui — ejecución de acciones cuando las otras capas no alcanzan

Uso:
    engine = create_screen_reader()
    texto = await engine.read_active_window()   # → "Excel: Libro1.xlsx. Celda A1 seleccionada..."
    await engine.type_text("hola mundo")
    await engine.navigate("next")
"""
from __future__ import annotations

import platform
import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from adapters.llm.ollama_adapter import OllamaAdapter

from .backends.base import ScreenReaderBackend

logger = logging.getLogger(__name__)


class ScreenReaderEngine:
    """
    Motor de lectura de pantalla multiplataforma.

    Abstrae el backend específico del SO y expone una interfaz uniforme
    que el ToolDispatcher y el daemon pueden usar sin saber el OS.
    """

    def __init__(
        self,
        backend: ScreenReaderBackend,
        vision_adapter: "OllamaAdapter | None" = None,
    ) -> None:
        self._backend = backend
        self._vision = vision_adapter  # OllamaAdapter con modelo multimodal

    # ── Lectura ───────────────────────────────────────────────────────────────

    async def read_active_window(self) -> str:
        """
        Lee el contenido de la ventana activa.
        Si el backend falla, usa Vision como fallback.
        """
        if self._backend.is_available():
            result = await self._backend.read_active_window()
            if result:
                return result

        return await self._vision_fallback("Describí brevemente el contenido de esta ventana.")

    async def read_focused_element(self) -> str:
        """
        Lee el elemento de UI que tiene el foco (campo activo, celda, botón, etc.).
        """
        if self._backend.is_available():
            result = await self._backend.read_focused_element()
            if result:
                return result

        return await self._vision_fallback("¿Qué elemento tiene el foco en esta pantalla?")

    async def describe_screen(self, custom_prompt: str = "") -> str:
        """
        Descripción completa de la pantalla usando Gemma 4 Vision.
        Siempre usa el modelo multimodal — no la Accessibility API.
        Útil para: "¿qué hay en pantalla?", verificación visual, apps Electron.
        """
        return await self._vision_fallback(custom_prompt)

    # ── Navegación ────────────────────────────────────────────────────────────

    async def navigate(self, direction: str) -> str:
        """
        Navega la UI.
        direction: "next" | "prev" | "up" | "down" | "tab" | "shift_tab"
        Devuelve el texto del nuevo elemento enfocado.
        """
        if self._backend.is_available():
            return await self._backend.navigate(direction)

        # Fallback: pyautogui directo
        import pyautogui
        key_map = {
            "next": "tab", "prev": ("shift", "tab"),
            "tab": "tab", "shift_tab": ("shift", "tab"),
            "up": "up", "down": "down",
        }
        key = key_map.get(direction, "tab")
        if isinstance(key, tuple):
            pyautogui.hotkey(*key)
        else:
            pyautogui.press(key)
        return ""

    # ── Acciones ──────────────────────────────────────────────────────────────

    async def click_element(self, description: str) -> bool:
        """
        Hace click en el elemento que mejor coincide con la descripción.
        Ej: "el botón Guardar", "el menú Archivo", "la celda A1"
        """
        if self._backend.is_available():
            result = await self._backend.click_element(description)
            if result:
                return True

        logger.warning(f"click_element: no encontré '{description}' via Accessibility API")
        return False

    async def type_text(self, text: str) -> None:
        """Escribe texto en el elemento activo."""
        if self._backend.is_available():
            await self._backend.type_text(text)
        else:
            import pyautogui
            pyautogui.typewrite(text, interval=0.03)

    async def press_shortcut(self, keys: str) -> None:
        """
        Ejecuta un atajo de teclado.
        Ej: "ctrl+s", "alt+f4", "cmd+c"
        """
        import pyautogui
        parts = [k.strip() for k in keys.lower().split("+")]
        # Normalizar "cmd" → "command" en Mac, "win" → "winleft" en Windows
        normalized = []
        for p in parts:
            if p == "cmd":
                normalized.append("command")
            elif p == "win":
                normalized.append("winleft")
            else:
                normalized.append(p)
        pyautogui.hotkey(*normalized)

    # ── Contexto para Gemma ───────────────────────────────────────────────────

    async def get_ui_tree(self) -> dict:
        """
        Devuelve el árbol de UI de la ventana activa como dict.
        Gemma 4 puede razonar sobre este árbol para decidir qué acción tomar.
        """
        if self._backend.is_available():
            return await self._backend.get_ui_tree()
        return {}

    # ── Fallback Vision ───────────────────────────────────────────────────────

    async def _vision_fallback(self, prompt: str = "") -> str:
        if self._vision is None:
            return "Señor, el backend de accesibilidad no está disponible y no hay modelo de visión configurado."

        from .vision_fallback import describe_screen
        return await describe_screen(self._vision, prompt)


# ── Factory ───────────────────────────────────────────────────────────────────

def create_screen_reader(
    vision_adapter: "OllamaAdapter | None" = None,
) -> ScreenReaderEngine:
    """
    Crea el ScreenReaderEngine correcto para el SO actual.

    Args:
        vision_adapter: instancia de OllamaAdapter con modelo multimodal.
                        Si es None, el fallback de visión no está disponible.
    """
    os_name = platform.system()

    if os_name == "Darwin":
        from .backends.macos import MacOSBackend
        backend: ScreenReaderBackend = MacOSBackend()
        logger.info("ScreenReaderEngine: backend macOS (NSAccessibility)")

    elif os_name == "Windows":
        from .backends.windows import WindowsBackend
        backend = WindowsBackend()
        logger.info("ScreenReaderEngine: backend Windows (UI Automation)")

    else:
        # Linux: fallback a Vision únicamente por ahora
        # TODO: implementar LinuxBackend con pyatspi
        from .backends.base import ScreenReaderBackend as _Base

        class _NullBackend(_Base):
            def is_available(self) -> bool: return False
            async def read_active_window(self) -> str: return ""
            async def read_focused_element(self) -> str: return ""
            async def navigate(self, direction: str) -> str: return ""
            async def click_element(self, description: str) -> bool: return False
            async def type_text(self, text: str) -> None: pass
            async def get_ui_tree(self) -> dict: return {}

        backend = _NullBackend()
        logger.warning("ScreenReaderEngine: Linux sin backend nativo — solo Vision fallback")

    return ScreenReaderEngine(backend=backend, vision_adapter=vision_adapter)
