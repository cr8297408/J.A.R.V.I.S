"""
Backend Windows — UI Automation via pywinauto.

Lee el árbol de accesibilidad igual que JAWS/NVDA.
Instalación: pip install pywinauto

NOTA: pywinauto solo funciona en Windows. Este módulo no se importa en Mac/Linux.
"""
from __future__ import annotations

import asyncio
import logging

from .base import ScreenReaderBackend

logger = logging.getLogger(__name__)


class WindowsBackend(ScreenReaderBackend):
    """
    Backend Windows usando pywinauto + UI Automation.

    pywinauto expone el árbol completo de UI de cualquier aplicación Windows
    a través de la misma API que usa JAWS internamente.
    """

    def __init__(self) -> None:
        self._available = self._check_dependencies()

    def is_available(self) -> bool:
        return self._available

    def _check_dependencies(self) -> bool:
        try:
            import pywinauto  # noqa: F401
            return True
        except ImportError:
            logger.warning(
                "pywinauto no está instalado. Instalá con: pip install pywinauto"
            )
            return False

    def _get_active_window(self):
        """Obtiene la ventana activa usando pywinauto."""
        from pywinauto import Desktop
        desktop = Desktop(backend="uia")
        # Obtener la ventana con foco
        try:
            return desktop.window(active_only=True)
        except Exception:
            # Fallback: primera ventana encontrada
            windows = desktop.windows()
            return windows[0] if windows else None

    async def read_active_window(self) -> str:
        """Lee el contenido textual de la ventana activa."""
        if not self._available:
            return "Backend de accesibilidad no disponible en Windows. Instalá pywinauto."

        try:
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(None, self._sync_read_active_window)
        except Exception as e:
            logger.error(f"WindowsBackend.read_active_window error: {e}")
            return ""

    def _sync_read_active_window(self) -> str:
        window = self._get_active_window()
        if not window:
            return "No hay ventana activa."

        try:
            title = window.window_text() or "ventana sin título"
            # Recolectar todos los textos del árbol de la ventana
            texts = []
            for ctrl in window.descendants():
                try:
                    text = ctrl.window_text()
                    if text and text.strip():
                        texts.append(text.strip())
                except Exception:
                    continue

            unique = list(dict.fromkeys(texts))[:40]
            content = ". ".join(unique)
            return f"{title}: {content}" if content else f"Ventana '{title}' sin contenido textual."
        except Exception as e:
            logger.error(f"WindowsBackend._sync_read_active_window error: {e}")
            return ""

    async def read_focused_element(self) -> str:
        """Lee el elemento de UI que tiene el foco."""
        if not self._available:
            return ""

        try:
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(None, self._sync_read_focused)
        except Exception as e:
            logger.error(f"WindowsBackend.read_focused_element error: {e}")
            return ""

    def _sync_read_focused(self) -> str:
        try:
            from pywinauto import Desktop
            desktop = Desktop(backend="uia")
            focused = desktop.get_active()
            if not focused:
                return "No hay elemento enfocado."

            parts = []
            text = focused.window_text()
            if text:
                parts.append(text)

            ctrl_type = focused.friendly_class_name()
            if ctrl_type:
                parts.append(f"tipo: {ctrl_type}")

            return ". ".join(parts) if parts else "Elemento sin texto."
        except Exception as e:
            logger.error(f"WindowsBackend._sync_read_focused error: {e}")
            return ""

    async def navigate(self, direction: str) -> str:
        """Navega la UI enviando teclas."""
        import pyautogui

        key_map = {
            "next":      "tab",
            "prev":      ("shift", "tab"),
            "tab":       "tab",
            "shift_tab": ("shift", "tab"),
            "up":        "up",
            "down":      "down",
        }
        key = key_map.get(direction, "tab")

        try:
            if isinstance(key, tuple):
                pyautogui.hotkey(*key)
            else:
                pyautogui.press(key)

            await asyncio.sleep(0.1)
            return await self.read_focused_element()
        except Exception as e:
            logger.error(f"WindowsBackend.navigate error: {e}")
            return ""

    async def click_element(self, description: str) -> bool:
        """Busca y clickea un elemento por descripción de texto."""
        if not self._available:
            return False

        try:
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(None, self._sync_click, description)
        except Exception as e:
            logger.error(f"WindowsBackend.click_element error: {e}")
            return False

    def _sync_click(self, description: str) -> bool:
        window = self._get_active_window()
        if not window:
            return False

        target = description.lower()
        try:
            for ctrl in window.descendants():
                try:
                    text = ctrl.window_text()
                    if text and target in text.lower():
                        ctrl.click_input()
                        return True
                except Exception:
                    continue
        except Exception as e:
            logger.error(f"WindowsBackend._sync_click error: {e}")

        return False

    async def type_text(self, text: str) -> None:
        """Escribe texto en el elemento activo."""
        try:
            import pyautogui
            pyautogui.typewrite(text, interval=0.03)
        except Exception as e:
            logger.error(f"WindowsBackend.type_text error: {e}")

    async def get_ui_tree(self) -> dict:
        """Devuelve el árbol de accesibilidad de la ventana activa."""
        if not self._available:
            return {}

        try:
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(None, self._sync_get_tree)
        except Exception as e:
            logger.error(f"WindowsBackend.get_ui_tree error: {e}")
            return {}

    def _sync_get_tree(self) -> dict:
        window = self._get_active_window()
        if not window:
            return {}

        def node_to_dict(ctrl, depth: int = 0) -> dict:
            if depth > 4:
                return {}
            node: dict = {}
            text = ctrl.window_text()
            if text:
                node["text"] = text
            ctrl_type = ctrl.friendly_class_name()
            if ctrl_type:
                node["type"] = ctrl_type
            try:
                children = [
                    node_to_dict(c, depth + 1)
                    for c in ctrl.children()
                    if node_to_dict(c, depth + 1)
                ]
                if children:
                    node["children"] = children
            except Exception:
                pass
            return node

        return node_to_dict(window)
