"""
HotkeyListener — Atajo de teclado global para detener ejecuciones de Jarvis.

Reemplaza el barge-in por VAD (sensible al ruido de fondo) con un shortcut
deliberado del teclado.

Shortcut por defecto: Ctrl+Shift+T
Configurable vía variable de entorno: JARVIS_STOP_HOTKEY
  Ej: JARVIS_STOP_HOTKEY="<ctrl>+<shift>+t"

Nota macOS: pynput requiere permiso de Accesibilidad.
  Sistema > Privacidad y Seguridad > Accesibilidad → agregar la terminal.
"""
from __future__ import annotations

import logging
import os
import threading
from typing import Callable

logger = logging.getLogger(__name__)

DEFAULT_HOTKEY = "<ctrl>+<shift>+t"


class HotkeyListener:
    """
    Escucha un hotkey global y llama a `on_stop` cuando se presiona.
    Corre en un hilo demonio para no bloquear el event loop principal.
    """

    def __init__(
        self,
        on_stop: Callable[[], None],
        hotkey: str | None = None,
    ) -> None:
        self._on_stop = on_stop
        self._hotkey = hotkey or os.getenv("JARVIS_STOP_HOTKEY", DEFAULT_HOTKEY)
        self._thread: threading.Thread | None = None
        self._listener = None

    # ── API pública ───────────────────────────────────────────────────────────

    def start(self) -> None:
        """Inicia el listener en un hilo demonio."""
        self._thread = threading.Thread(target=self._run, daemon=True, name="hotkey-listener")
        self._thread.start()
        logger.info(f"[Hotkey] Escuchando '{self._hotkey}' para detener ejecución.")

    def stop(self) -> None:
        """Detiene el listener limpiamente."""
        if self._listener is not None:
            try:
                self._listener.stop()
            except Exception:
                pass

    # ── Internals ─────────────────────────────────────────────────────────────

    def _run(self) -> None:
        try:
            from pynput import keyboard

            def _trigger():
                logger.info(f"[Hotkey] '{self._hotkey}' presionado — deteniendo ejecución.")
                self._on_stop()

            self._listener = keyboard.GlobalHotKeys({self._hotkey: _trigger})
            self._listener.run()

        except ImportError:
            logger.error(
                "[Hotkey] pynput no instalado. "
                "Ejecutá: pip install pynput"
            )
        except Exception as e:
            logger.error(f"[Hotkey] Error inesperado: {e}")
