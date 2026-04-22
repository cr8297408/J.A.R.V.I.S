"""
Backend macOS — NSAccessibility via pyobjc.

Lee el árbol de accesibilidad del sistema igual que VoiceOver.
No requiere permisos especiales más allá de Accessibility en System Preferences.

Instalación: pip install pyobjc-framework-Cocoa pyobjc-framework-ApplicationServices

IMPORTANTE: En macOS, la app que usa este backend necesita tener permiso de
Accessibility habilitado en: Configuración del Sistema → Privacidad y Seguridad → Accesibilidad.
"""
from __future__ import annotations

import asyncio
import logging

from .base import ScreenReaderBackend

logger = logging.getLogger(__name__)


class MacOSBackend(ScreenReaderBackend):
    """
    Backend macOS usando NSAccessibility (pyobjc).

    La API de Accessibility de Apple expone toda la UI como un árbol de AXUIElement.
    Cada elemento tiene atributos: AXTitle, AXValue, AXDescription, AXRole, etc.
    """

    def __init__(self) -> None:
        self._ax = None       # ApplicationServices.AXUIElement
        self._appkit = None   # AppKit.NSWorkspace
        self._available = self._check_dependencies()

    def is_available(self) -> bool:
        return self._available

    def _check_dependencies(self) -> bool:
        try:
            import ApplicationServices  # noqa: F401
            import AppKit               # noqa: F401
            return True
        except ImportError:
            logger.warning(
                "pyobjc no está instalado. Instalá con: "
                "pip install pyobjc-framework-Cocoa pyobjc-framework-ApplicationServices"
            )
            return False

    def _get_frontmost_ax_element(self):
        """Obtiene el AXUIElement de la app en primer plano."""
        import AppKit
        import ApplicationServices as AS

        workspace = AppKit.NSWorkspace.sharedWorkspace()
        app = workspace.frontmostApplication()
        pid = app.processIdentifier()
        return AS.AXUIElementCreateApplication(pid)

    def _get_attribute(self, element, attr: str):
        """Lee un atributo de un AXUIElement."""
        import ApplicationServices as AS
        err, value = AS.AXUIElementCopyAttributeValue(element, attr, None)
        if err == AS.kAXErrorSuccess:
            return value
        return None

    def _collect_text(self, element, depth: int = 0, max_depth: int = 6) -> list[str]:
        """Recorre el árbol de accesibilidad y recolecta texto visible."""
        if depth > max_depth:
            return []

        import ApplicationServices as AS

        texts = []

        for attr in ("AXValue", "AXTitle", "AXDescription", "AXLabel"):
            value = self._get_attribute(element, attr)
            if value and isinstance(value, str) and value.strip():
                texts.append(value.strip())

        # Recorrer hijos
        children = self._get_attribute(element, "AXChildren")
        if children:
            for child in children:
                texts.extend(self._collect_text(child, depth + 1, max_depth))

        return texts

    async def read_active_window(self) -> str:
        """Lee el contenido textual de la ventana activa."""
        if not self._available:
            return "Backend de accesibilidad no disponible. Instalá pyobjc."

        try:
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(None, self._sync_read_active_window)
        except Exception as e:
            logger.error(f"MacOSBackend.read_active_window error: {e}")
            return ""

    def _sync_read_active_window(self) -> str:
        import AppKit
        workspace = AppKit.NSWorkspace.sharedWorkspace()
        app = workspace.frontmostApplication()
        app_name = app.localizedName() or "aplicación desconocida"

        ax_app = self._get_frontmost_ax_element()
        texts = self._collect_text(ax_app)

        unique = list(dict.fromkeys(t for t in texts if t))  # dedup preservando orden
        content = ". ".join(unique[:30])  # límite razonable para TTS

        return f"{app_name}: {content}" if content else f"Ventana de {app_name} sin contenido textual."

    async def read_focused_element(self) -> str:
        """Lee el elemento de UI que tiene el foco actualmente."""
        if not self._available:
            return ""

        try:
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(None, self._sync_read_focused)
        except Exception as e:
            logger.error(f"MacOSBackend.read_focused_element error: {e}")
            return ""

    def _sync_read_focused(self) -> str:
        import ApplicationServices as AS

        ax_app = self._get_frontmost_ax_element()
        focused = self._get_attribute(ax_app, "AXFocusedUIElement")
        if not focused:
            return "No hay elemento enfocado."

        parts = []
        for attr in ("AXRole", "AXTitle", "AXValue", "AXDescription"):
            val = self._get_attribute(focused, attr)
            if val and isinstance(val, str):
                parts.append(val)

        return ". ".join(parts) if parts else "Elemento sin texto."

    async def navigate(self, direction: str) -> str:
        """Navega la UI enviando teclas de accesibilidad."""
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
            logger.error(f"MacOSBackend.navigate error: {e}")
            return ""

    async def click_element(self, description: str) -> bool:
        """
        Busca un elemento por descripción en el árbol de accesibilidad y lo clickea.
        """
        if not self._available:
            return False

        try:
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(None, self._sync_click, description)
        except Exception as e:
            logger.error(f"MacOSBackend.click_element error: {e}")
            return False

    def _sync_click(self, description: str) -> bool:
        import ApplicationServices as AS

        ax_app = self._get_frontmost_ax_element()
        element = self._find_element_by_text(ax_app, description.lower())
        if not element:
            return False

        err = AS.AXUIElementPerformAction(element, "AXPress")
        return err == AS.kAXErrorSuccess

    def _find_element_by_text(self, element, target: str, depth: int = 0):
        """Busca recursivamente un elemento cuyo texto contenga el target."""
        if depth > 8:
            return None

        import ApplicationServices as AS

        for attr in ("AXTitle", "AXDescription", "AXLabel", "AXValue"):
            val = self._get_attribute(element, attr)
            if val and isinstance(val, str) and target in val.lower():
                return element

        children = self._get_attribute(element, "AXChildren")
        if children:
            for child in children:
                found = self._find_element_by_text(child, target, depth + 1)
                if found:
                    return found

        return None

    async def type_text(self, text: str) -> None:
        """Escribe texto en el elemento activo."""
        try:
            import pyautogui
            pyautogui.typewrite(text, interval=0.03)
        except Exception as e:
            logger.error(f"MacOSBackend.type_text error: {e}")

    async def get_ui_tree(self) -> dict:
        """Devuelve el árbol de accesibilidad como dict (para que Gemma razone)."""
        if not self._available:
            return {}

        try:
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(None, self._sync_get_tree)
        except Exception as e:
            logger.error(f"MacOSBackend.get_ui_tree error: {e}")
            return {}

    def _sync_get_tree(self, element=None, depth: int = 0, max_depth: int = 4) -> dict:
        import AppKit

        if element is None:
            workspace = AppKit.NSWorkspace.sharedWorkspace()
            app = workspace.frontmostApplication()
            app_name = app.localizedName() or "unknown"
            element = self._get_frontmost_ax_element()
            root = {"app": app_name, "children": []}
            root["children"] = [self._sync_get_tree(element, 1, max_depth)]
            return root

        if depth > max_depth:
            return {}

        node: dict = {}
        for attr in ("AXRole", "AXTitle", "AXValue", "AXDescription"):
            val = self._get_attribute(element, attr)
            if val and isinstance(val, str):
                node[attr.replace("AX", "").lower()] = val

        children = self._get_attribute(element, "AXChildren")
        if children:
            child_nodes = [
                self._sync_get_tree(c, depth + 1, max_depth)
                for c in children
                if self._sync_get_tree(c, depth + 1, max_depth)
            ]
            if child_nodes:
                node["children"] = child_nodes

        return node
