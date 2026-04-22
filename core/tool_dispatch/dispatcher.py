"""
ToolDispatcher — ejecuta las herramientas de PC que Gemma 4 decide usar.

Flujo:
    1. El daemon pasa el comando de voz a gemma4:pc via OllamaAdapter
    2. Gemma 4 responde con un tool_call (function calling)
    3. El dispatcher recibe el tool_call y ejecuta la acción real
    4. Devuelve el resultado al daemon para que lo narre por TTS

El dispatcher no toma decisiones — solo ejecuta.
Gemma 4 decide qué hacer; el dispatcher lo hace posible.
"""
from __future__ import annotations

import asyncio
import json
import logging
import subprocess
import platform
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from core.screen_reader.engine import ScreenReaderEngine

from .registry import REQUIRES_CONFIRMATION, DESTRUCTIVE_SHORTCUTS

logger = logging.getLogger(__name__)


class ToolDispatcher:
    """
    Ejecuta herramientas de PC en respuesta a tool_calls de Gemma 4.

    Uso:
        dispatcher = ToolDispatcher(screen_reader=engine)
        result = await dispatcher.execute("type_text", {"text": "hola"})
        # → "Señor, texto escrito."
    """

    def __init__(
        self,
        screen_reader: "ScreenReaderEngine",
        confirmation_callback=None,
    ) -> None:
        """
        Args:
            screen_reader: instancia de ScreenReaderEngine.
            confirmation_callback: función async que pide confirmación vocal.
                Firma: async (message: str) -> bool
                Si None, las acciones que requieren confirmación se bloquean.
        """
        self._sr = screen_reader
        self._confirm = confirmation_callback

    async def execute(self, tool_name: str, args: dict) -> str:
        """
        Ejecuta una herramienta y devuelve un mensaje para TTS.

        Args:
            tool_name: nombre de la herramienta (según registry.py)
            args: argumentos de la herramienta

        Returns:
            Texto listo para TTS. Siempre devuelve algo.
        """
        logger.info(f"ToolDispatcher.execute: {tool_name}({args})")

        # Acciones que requieren confirmación vocal
        if tool_name in REQUIRES_CONFIRMATION:
            if not await self._request_confirmation(tool_name, args):
                return "Señor, acción cancelada."

        handler = self._handlers.get(tool_name)
        if not handler:
            logger.warning(f"Herramienta desconocida: {tool_name}")
            return f"Señor, la herramienta '{tool_name}' no está implementada."

        try:
            return await handler(self, args)
        except Exception as e:
            logger.error(f"ToolDispatcher error en {tool_name}: {e}")
            return f"Señor, hubo un error al ejecutar la acción: {e}"

    async def execute_tool_call(self, tool_call: dict) -> str:
        """
        Interfaz para tool_calls en formato OpenAI:
            {"name": "...", "arguments": "{...}"}
        """
        name = tool_call.get("name", "")
        raw_args = tool_call.get("arguments", "{}")
        try:
            args = json.loads(raw_args) if isinstance(raw_args, str) else raw_args
        except json.JSONDecodeError:
            args = {}
        return await self.execute(name, args)

    # ── Confirmación vocal ────────────────────────────────────────────────────

    async def _request_confirmation(self, tool_name: str, args: dict) -> bool:
        if self._confirm is None:
            logger.warning(f"Confirmación requerida para {tool_name} pero no hay callback.")
            return False

        messages = {
            "run_command": f"Señor, quiero ejecutar el comando: {args.get('command', '')}. ¿Procedo? Diga sí o no.",
            "close_app":   f"Señor, voy a cerrar {args.get('name', 'la ventana activa')}. ¿Procedo?",
        }
        msg = messages.get(tool_name, f"Señor, ¿confirma la acción {tool_name}?")
        return await self._confirm(msg)

    # ── Handlers ──────────────────────────────────────────────────────────────

    async def _handle_read_screen(self, args: dict) -> str:
        target = args.get("target", "active_window")
        if target == "active_window":
            content = await self._sr.read_active_window()
        elif target == "focused_element":
            content = await self._sr.read_focused_element()
        else:  # full_screen
            content = await self._sr.describe_screen()
        return content or "Señor, no hay contenido legible en este momento."

    async def _handle_navigate_ui(self, args: dict) -> str:
        direction = args.get("direction", "next")
        result = await self._sr.navigate(direction)
        return result or "Señor, navegué pero no encontré texto en el elemento."

    async def _handle_type_text(self, args: dict) -> str:
        text = args.get("text", "")
        clear_first = args.get("clear_first", False)
        if not text:
            return "Señor, no hay texto para escribir."
        if clear_first:
            import pyautogui
            pyautogui.hotkey("ctrl", "a")
            await asyncio.sleep(0.05)
        await self._sr.type_text(text)
        return f"Señor, escribí: {text[:50]}{'...' if len(text) > 50 else ''}."

    async def _handle_open_app(self, args: dict) -> str:
        name = args.get("name", "")
        if not name:
            return "Señor, no especificaste qué aplicación abrir."
        try:
            _open_application(name)
            await asyncio.sleep(0.8)  # Dale tiempo a la app para iniciarse
            return f"Señor, abrí {name}."
        except Exception as e:
            return f"Señor, no pude abrir {name}: {e}"

    async def _handle_close_app(self, args: dict) -> str:
        name = args.get("name", "")
        try:
            if name:
                _close_application(name)
                return f"Señor, cerré {name}."
            else:
                import pyautogui
                os_name = platform.system()
                if os_name == "Darwin":
                    pyautogui.hotkey("cmd", "w")
                else:
                    pyautogui.hotkey("alt", "f4")
                return "Señor, cerré la ventana activa."
        except Exception as e:
            return f"Señor, no pude cerrar la aplicación: {e}"

    async def _handle_switch_window(self, args: dict) -> str:
        name = args.get("name", "")
        if not name:
            return "Señor, no especificaste a qué ventana cambiar."
        try:
            _switch_to_window(name)
            await asyncio.sleep(0.3)
            return f"Señor, cambié a {name}."
        except Exception as e:
            return f"Señor, no encontré la ventana {name}: {e}"

    async def _handle_press_shortcut(self, args: dict) -> str:
        keys = args.get("keys", "")
        if not keys:
            return "Señor, no especificaste el atajo."
        # Advertir en atajos destructivos (run_command ya tiene confirmación,
        # pero estos pueden cerrar cosas sin ser run_command)
        if keys.lower() in DESTRUCTIVE_SHORTCUTS:
            if not await self._request_confirmation("press_shortcut", {"keys": keys}):
                return "Señor, atajo cancelado."
        await self._sr.press_shortcut(keys)
        return f"Señor, ejecuté el atajo {keys}."

    async def _handle_click_element(self, args: dict) -> str:
        description = args.get("description", "")
        if not description:
            return "Señor, no especificaste qué elemento clickear."
        found = await self._sr.click_element(description)
        if found:
            return f"Señor, hice click en {description}."
        return f"Señor, no encontré el elemento '{description}' en pantalla."

    async def _handle_copy_selection(self, args: dict) -> str:
        import pyautogui
        os_name = platform.system()
        if os_name == "Darwin":
            pyautogui.hotkey("cmd", "c")
        else:
            pyautogui.hotkey("ctrl", "c")
        return "Señor, copié el texto seleccionado."

    async def _handle_paste_text(self, args: dict) -> str:
        import pyautogui
        os_name = platform.system()
        if os_name == "Darwin":
            pyautogui.hotkey("cmd", "v")
        else:
            pyautogui.hotkey("ctrl", "v")
        return "Señor, pegué el texto del portapapeles."

    async def _handle_describe_screen(self, args: dict) -> str:
        focus = args.get("focus", "")
        prompt = f"Describí lo que hay en pantalla. {'Enfocate en: ' + focus if focus else ''}"
        return await self._sr.describe_screen(prompt)

    async def _handle_run_command(self, args: dict) -> str:
        command = args.get("command", "")
        if not command:
            return "Señor, no especificaste qué comando ejecutar."
        try:
            result = subprocess.run(
                command, shell=True, capture_output=True, text=True, timeout=30
            )
            output = result.stdout.strip() or result.stderr.strip()
            if result.returncode == 0:
                return f"Señor, el comando terminó correctamente. {output[:200] if output else ''}"
            else:
                return f"Señor, el comando falló con código {result.returncode}. {output[:200]}"
        except subprocess.TimeoutExpired:
            return "Señor, el comando tardó demasiado y fue cancelado."
        except Exception as e:
            return f"Señor, error al ejecutar el comando: {e}"

    # ── Tabla de handlers ─────────────────────────────────────────────────────

    _handlers = {
        "read_screen":      _handle_read_screen,
        "navigate_ui":      _handle_navigate_ui,
        "type_text":        _handle_type_text,
        "open_app":         _handle_open_app,
        "close_app":        _handle_close_app,
        "switch_window":    _handle_switch_window,
        "press_shortcut":   _handle_press_shortcut,
        "click_element":    _handle_click_element,
        "copy_selection":   _handle_copy_selection,
        "paste_text":       _handle_paste_text,
        "describe_screen":  _handle_describe_screen,
        "run_command":      _handle_run_command,
    }


# ── Helpers de plataforma ─────────────────────────────────────────────────────

def _open_application(name: str) -> None:
    os_name = platform.system()
    if os_name == "Darwin":
        subprocess.Popen(["open", "-a", name])
    elif os_name == "Windows":
        subprocess.Popen(["start", name], shell=True)
    else:
        subprocess.Popen([name.lower()])


def _close_application(name: str) -> None:
    os_name = platform.system()
    if os_name == "Darwin":
        subprocess.run(["osascript", "-e", f'quit app "{name}"'])
    elif os_name == "Windows":
        subprocess.run(["taskkill", "/F", "/IM", f"{name}.exe"])
    else:
        subprocess.run(["pkill", "-f", name])


def _switch_to_window(name: str) -> None:
    os_name = platform.system()
    if os_name == "Darwin":
        subprocess.run(
            ["osascript", "-e", f'tell application "{name}" to activate']
        )
    elif os_name == "Windows":
        try:
            import pygetwindow as gw
            windows = gw.getWindowsWithTitle(name)
            if windows:
                windows[0].activate()
        except ImportError:
            logger.warning("pygetwindow no está instalado: pip install pygetwindow")
    else:
        subprocess.run(["wmctrl", "-a", name])
