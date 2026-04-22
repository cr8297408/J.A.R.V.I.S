"""
Screen Reader Backend — Linux (AT-SPI via pyatspi).

Usa el mismo protocolo de Accessibility Tree que JAWS/NVDA pero en Linux.
AT-SPI (Assistive Technology Service Provider Interface) es el estándar de
accesibilidad en Linux/GTK — el mismo que usa Orca screen reader.

Requiere: pip install pyatspi
"""
from __future__ import annotations

import asyncio
import logging
from typing import Any

from .base import ScreenReaderBackend

logger = logging.getLogger(__name__)


class LinuxScreenReaderBackend(ScreenReaderBackend):
    """
    Backend de accesibilidad para Linux usando AT-SPI.

    AT-SPI funciona con apps GTK, Qt y cualquier toolkit que exponga
    el árbol de accesibilidad del SO — igual que NSAccessibility en macOS.
    """

    def is_available(self) -> bool:
        try:
            import pyatspi  # noqa: F401
            return True
        except ImportError:
            return False

    async def read_active_window(self) -> str:
        """Lee el contenido textual de la ventana activa vía AT-SPI."""
        return await asyncio.get_event_loop().run_in_executor(None, self._read_active_window_sync)

    def _read_active_window_sync(self) -> str:
        try:
            import pyatspi

            desktop = pyatspi.Registry.getDesktop(0)
            texts: list[str] = []

            for app in desktop:
                if app is None:
                    continue
                for window in app:
                    if window is None:
                        continue
                    states = window.getState()
                    if states.contains(pyatspi.STATE_ACTIVE):
                        self._collect_text(window, texts)
                        return "\n".join(t for t in texts if t.strip()) or "(ventana activa sin texto)"

            return "(no se encontró ventana activa)"
        except Exception as e:
            logger.error(f"LinuxBackend.read_active_window error: {e}")
            return f"(error leyendo ventana: {e})"

    def _collect_text(self, node: Any, result: list[str], depth: int = 0) -> None:
        """Recorre el árbol AT-SPI recursivamente y recolecta texto."""
        if depth > 20:
            return
        try:
            name = node.name or ""
            if name.strip():
                result.append(name.strip())

            # Si el nodo implementa la interfaz Text, leer el texto directamente
            try:
                text_iface = node.queryText()
                text = text_iface.getText(0, -1)
                if text and text.strip() and text.strip() != name.strip():
                    result.append(text.strip())
            except Exception:
                pass

            for child in node:
                if child is not None:
                    self._collect_text(child, result, depth + 1)
        except Exception:
            pass

    async def read_focused_element(self) -> str:
        """Lee el elemento de UI con el foco actual."""
        return await asyncio.get_event_loop().run_in_executor(None, self._read_focused_sync)

    def _read_focused_sync(self) -> str:
        try:
            import pyatspi

            desktop = pyatspi.Registry.getDesktop(0)
            for app in desktop:
                if app is None:
                    continue
                focused = self._find_focused(app)
                if focused:
                    name = focused.name or ""
                    try:
                        text_iface = focused.queryText()
                        text = text_iface.getText(0, -1)
                        return f"{name}: {text}".strip(": ")
                    except Exception:
                        return name or "(elemento sin texto)"

            return "(sin foco detectado)"
        except Exception as e:
            logger.error(f"LinuxBackend.read_focused_element error: {e}")
            return f"(error: {e})"

    def _find_focused(self, node: Any, depth: int = 0) -> Any | None:
        """Busca recursivamente el nodo con STATE_FOCUSED."""
        if depth > 20:
            return None
        try:
            import pyatspi
            states = node.getState()
            if states.contains(pyatspi.STATE_FOCUSED):
                return node
            for child in node:
                if child is not None:
                    found = self._find_focused(child, depth + 1)
                    if found:
                        return found
        except Exception:
            pass
        return None

    async def navigate(self, direction: str) -> str:
        """Navega la UI enviando teclas de accesibilidad."""
        import pyautogui

        key_map = {
            "next":      "tab",
            "prev":      ["shift", "tab"],
            "up":        "up",
            "down":      "down",
            "tab":       "tab",
            "shift_tab": ["shift", "tab"],
        }
        keys = key_map.get(direction, "tab")
        if isinstance(keys, list):
            await asyncio.to_thread(pyautogui.hotkey, *keys)
        else:
            await asyncio.to_thread(pyautogui.press, keys)

        await asyncio.sleep(0.1)
        return await self.read_focused_element()

    async def click_element(self, description: str) -> bool:
        """Hace click en el elemento que mejor coincida con la descripción."""
        return await asyncio.get_event_loop().run_in_executor(
            None, self._click_element_sync, description
        )

    def _click_element_sync(self, description: str) -> bool:
        try:
            import pyatspi

            desktop = pyatspi.Registry.getDesktop(0)
            desc_lower = description.lower()

            for app in desktop:
                if app is None:
                    continue
                element = self._find_by_text(app, desc_lower)
                if element:
                    try:
                        action_iface = element.queryAction()
                        for i in range(action_iface.nActions):
                            if action_iface.getName(i).lower() in ("click", "press", "activate"):
                                action_iface.doAction(i)
                                return True
                    except Exception:
                        pass
            return False
        except Exception as e:
            logger.error(f"LinuxBackend.click_element error: {e}")
            return False

    def _find_by_text(self, node: Any, text_lower: str, depth: int = 0) -> Any | None:
        if depth > 20:
            return None
        try:
            name = (node.name or "").lower()
            if text_lower in name:
                return node
            for child in node:
                if child is not None:
                    found = self._find_by_text(child, text_lower, depth + 1)
                    if found:
                        return found
        except Exception:
            pass
        return None

    async def type_text(self, text: str) -> None:
        """Escribe texto en el elemento activo."""
        import pyautogui
        await asyncio.to_thread(pyautogui.typewrite, text, interval=0.02)

    async def get_ui_tree(self) -> dict:
        """Devuelve el árbol de accesibilidad de la ventana activa."""
        return await asyncio.get_event_loop().run_in_executor(None, self._get_tree_sync)

    def _get_tree_sync(self) -> dict:
        try:
            import pyatspi

            desktop = pyatspi.Registry.getDesktop(0)
            for app in desktop:
                if app is None:
                    continue
                for window in app:
                    if window is None:
                        continue
                    states = window.getState()
                    if states.contains(pyatspi.STATE_ACTIVE):
                        return self._node_to_dict(window)
            return {}
        except Exception as e:
            logger.error(f"LinuxBackend.get_ui_tree error: {e}")
            return {}

    def _node_to_dict(self, node: Any, depth: int = 0) -> dict:
        if depth > 10:
            return {}
        try:
            result: dict = {
                "name": node.name or "",
                "role": node.getRoleName() or "",
                "children": [],
            }
            for child in node:
                if child is not None:
                    result["children"].append(self._node_to_dict(child, depth + 1))
            return result
        except Exception:
            return {}
