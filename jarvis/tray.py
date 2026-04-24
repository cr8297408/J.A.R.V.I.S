"""
J.A.R.V.I.S. — System Tray Desktop App.

Cross-platform entry point for accessibility. No terminal required.
Users interact through the system tray icon: click to start/stop voice.

Supported platforms: macOS, Windows, Linux (requires libayatana-appindicator on GNOME).
"""
from __future__ import annotations

import logging
import os
import sys
import threading

logger = logging.getLogger(__name__)

# Ensure project root is on path when running as a bundled .app / .exe
_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_HERE)
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

# When frozen by PyInstaller, _ROOT points to a temp read-only dir.
# All user config lives in a platform-appropriate writable directory instead.
_FROZEN = getattr(sys, "frozen", False)


def _config_dir() -> str:
    """Returns the writable user config directory for J.A.R.V.I.S."""
    if sys.platform == "darwin":
        base = os.path.expanduser("~/Library/Application Support/JARVIS")
    elif sys.platform == "win32":
        base = os.path.join(os.getenv("APPDATA", os.path.expanduser("~")), "JARVIS")
    else:
        base = os.path.expanduser("~/.config/jarvis")
    os.makedirs(base, exist_ok=True)
    return base


def _env_path() -> str:
    """
    Returns the path to the .env config file.
    In dev mode: project root .env (existing behavior).
    In bundled mode: user config directory .env.
    """
    if _FROZEN:
        return os.path.join(_config_dir(), ".env")
    return os.path.join(_ROOT, ".env")


def _ensure_env_exists() -> None:
    """
    On first run of a bundled app, copy .env.example from the bundle
    to the user config directory so the user has a template to fill in.
    """
    if not _FROZEN:
        return
    target = _env_path()
    if os.path.exists(target):
        return
    # Look for .env.example inside the PyInstaller bundle
    example = os.path.join(getattr(sys, "_MEIPASS", _ROOT), ".env.example")
    if os.path.exists(example):
        import shutil
        shutil.copy(example, target)


def _require(package: str, install_hint: str) -> None:
    try:
        __import__(package)
    except ImportError:
        print(
            f"[J.A.R.V.I.S] Falta dependencia: {package}\n"
            f"  Instalá con: {install_hint}"
        )
        sys.exit(1)


_require("pystray", "pip install pystray")
_require("PIL", "pip install Pillow")

import pystray  # noqa: E402
from PIL import Image, ImageDraw  # noqa: E402


# ── Icon generation ────────────────────────────────────────────────────────────

def _make_icon(active: bool = False) -> Image.Image:
    """Generate tray icon in memory. Blue = idle, green = listening."""
    size = 64
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Background circle
    fill = (0, 200, 80, 255) if active else (0, 120, 220, 255)
    draw.ellipse((2, 2, size - 2, size - 2), fill=fill)

    # Microphone body (rect)
    draw.rounded_rectangle((22, 12, 42, 36), radius=8, fill=(255, 255, 255, 230))

    # Microphone stand (arc + line)
    draw.arc((16, 26, 48, 46), start=0, end=180, fill=(255, 255, 255, 230), width=3)
    draw.line((32, 46, 32, 54), fill=(255, 255, 255, 230), width=3)
    draw.line((24, 54, 40, 54), fill=(255, 255, 255, 230), width=3)

    # Green activity dot when active
    if active:
        draw.ellipse((44, 44, 58, 58), fill=(255, 255, 100, 255))

    return img


def _load_icon_file(active: bool = False) -> Image.Image:
    """Try to load a pre-generated icon file, fall back to generated icon."""
    assets_dir = os.path.join(_HERE, "assets")
    name = "icon_active.png" if active else "icon.png"
    path = os.path.join(assets_dir, name)
    if os.path.exists(path):
        try:
            return Image.open(path)
        except Exception:
            pass
    return _make_icon(active)


# ── Auto-start helpers ─────────────────────────────────────────────────────────

def _autostart_file() -> str | None:
    """Path to the auto-start config file for the current platform (None = registry on Win)."""
    if sys.platform == "darwin":
        return os.path.expanduser("~/Library/LaunchAgents/com.jarvis.voice.plist")
    if sys.platform == "win32":
        return None  # Uses Windows registry
    return os.path.expanduser("~/.config/autostart/jarvis.desktop")


def _is_autostart_enabled() -> bool:
    path = _autostart_file()
    if path:
        return os.path.exists(path)
    if sys.platform == "win32":
        try:
            import winreg  # type: ignore[import]
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows\CurrentVersion\Run",
                0,
                winreg.KEY_READ,
            )
            winreg.QueryValueEx(key, "JARVIS")
            winreg.CloseKey(key)
            return True
        except OSError:
            return False
    return False


def _enable_autostart() -> None:
    exe = sys.executable
    path = _autostart_file()

    if sys.platform == "darwin":
        plist = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
  "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key><string>com.jarvis.voice</string>
    <key>ProgramArguments</key>
    <array>
        <string>{exe}</string>
        <string>-m</string>
        <string>jarvis.tray</string>
    </array>
    <key>RunAtLoad</key><true/>
    <key>KeepAlive</key><false/>
    <key>StandardOutPath</key>
    <string>{os.path.expanduser("~/Library/Logs/jarvis.log")}</string>
    <key>StandardErrorPath</key>
    <string>{os.path.expanduser("~/Library/Logs/jarvis-error.log")}</string>
</dict>
</plist>"""
        assert path is not None
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w") as f:
            f.write(plist)
        import subprocess
        subprocess.run(["launchctl", "load", path], capture_output=True)

    elif sys.platform == "win32":
        import winreg  # type: ignore[import]
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Run",
            0,
            winreg.KEY_SET_VALUE,
        )
        winreg.SetValueEx(key, "JARVIS", 0, winreg.REG_SZ, f'"{exe}" -m jarvis.tray')
        winreg.CloseKey(key)

    else:  # Linux
        desktop = (
            "[Desktop Entry]\n"
            "Type=Application\n"
            "Name=J.A.R.V.I.S\n"
            f"Exec={exe} -m jarvis.tray\n"
            "Icon=microphone\n"
            "Hidden=false\n"
            "NoDisplay=false\n"
            "X-GNOME-Autostart-enabled=true\n"
        )
        assert path is not None
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w") as f:
            f.write(desktop)


def _disable_autostart() -> None:
    path = _autostart_file()

    if sys.platform == "darwin" and path and os.path.exists(path):
        import subprocess
        subprocess.run(["launchctl", "unload", path], capture_output=True)
        os.remove(path)

    elif sys.platform == "win32":
        try:
            import winreg  # type: ignore[import]
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows\CurrentVersion\Run",
                0,
                winreg.KEY_SET_VALUE,
            )
            winreg.DeleteValue(key, "JARVIS")
            winreg.CloseKey(key)
        except OSError:
            pass

    elif path and os.path.exists(path):
        os.remove(path)


# ── Quick TTS (pre-session, no full pipeline needed) ──────────────────────────

def _speak(text: str) -> None:
    """
    Speak text using platform-native TTS. Non-blocking.
    Used for startup narration and error reporting before the full session loads.
    """
    import shutil
    import subprocess
    try:
        if sys.platform == "darwin":
            subprocess.Popen(["say", "-v", "Mónica", text])
        elif sys.platform == "win32":
            script = (
                "Add-Type -AssemblyName System.Speech; "
                "$s = New-Object System.Speech.Synthesis.SpeechSynthesizer; "
                f'$s.Speak("{text.replace(chr(34), chr(39))}")'
            )
            subprocess.Popen(["powershell", "-Command", script])
        else:
            for cmd in ["espeak", "festival", "spd-say"]:
                if shutil.which(cmd):
                    subprocess.Popen([cmd, text])
                    break
    except Exception as exc:
        logger.warning("[TTS] No se pudo hablar: %s", exc)


# ── Pre-flight checks ──────────────────────────────────────────────────────────

_REQUIRED_PACKAGES = [
    ("pyaudio", "pyaudio"),
    ("webrtcvad", "webrtcvad"),
    ("openwakeword", "openwakeword"),
    ("numpy", "numpy"),
    ("dotenv", "python-dotenv"),
]


def _check_required_packages() -> list[str]:
    """Returns list of pip package names that are missing."""
    missing = []
    for module, pip_name in _REQUIRED_PACKAGES:
        try:
            __import__(module)
        except (ImportError, Exception):
            missing.append(pip_name)
    return missing


def _has_wakeword_models() -> bool:
    """True if at least one .onnx wake word model is present in any known cache dir."""
    import os as _os
    candidates = []

    # PyInstaller frozen context: models are bundled under _MEIPASS
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        meipass = sys._MEIPASS
        candidates += [
            _os.path.join(meipass, "openwakeword", "resources", "models"),
            _os.path.join(meipass, "openwakeword", "resources"),
        ]

    try:
        import openwakeword as _oww
        candidates.append(
            _os.path.join(_os.path.dirname(_oww.__file__), "resources", "models")
        )
    except ImportError:
        pass

    home = _os.path.expanduser("~")
    candidates += [
        _os.path.join(home, "Library", "Caches", "openwakeword"),           # macOS
        _os.path.join(_os.getenv("XDG_CACHE_HOME", _os.path.join(home, ".cache")), "openwakeword"),  # Linux
    ]
    if sys.platform == "win32":
        local = _os.getenv("LOCALAPPDATA", "")
        if local:
            candidates.append(_os.path.join(local, "openwakeword"))

    for path in candidates:
        if _os.path.isdir(path):
            try:
                if any(f.endswith(".onnx") for f in _os.listdir(path)):
                    return True
            except OSError:
                pass
    return False


def _request_mic_permission_macos() -> None:
    """
    On macOS 14+, opening a PyAudio stream triggers the mic permission dialog.
    We do a quick probe open/close so the dialog appears BEFORE the session starts,
    giving the user time to approve before openwakeword starts listening.
    """
    try:
        import pyaudio
        pa = pyaudio.PyAudio()
        stream = pa.open(
            format=pyaudio.paInt16,
            channels=1,
            rate=16000,
            input=True,
            frames_per_buffer=480,
        )
        stream.stop_stream()
        stream.close()
        pa.terminate()
    except Exception:
        pass  # If it fails here the real session will handle the error


# ── Session controller ─────────────────────────────────────────────────────────

class _TrayController:
    """Manages the Jarvis voice session lifecycle from the system tray."""

    def __init__(self) -> None:
        self._session = None
        self._thread: threading.Thread | None = None
        self._running = False
        self._icon: pystray.Icon | None = None
        self._panel = None  # Se asigna desde run_tray()

    # ── Notification ──────────────────────────────────────────────────────────

    def _notify(self, message: str) -> None:
        if self._icon:
            try:
                self._icon.notify(message, "J.A.R.V.I.S")
            except Exception:
                pass

    # ── Voice session ─────────────────────────────────────────────────────────

    def start_voice(self, icon: pystray.Icon, item: pystray.MenuItem) -> None:
        if self._running:
            self._notify("J.A.R.V.I.S ya está activo")
            return

        self._running = True
        icon.icon = _load_icon_file(active=True)
        icon.update_menu()

        def _run() -> None:
            try:
                _speak("Iniciando Jarvis.")

                # ── 1. Load config ────────────────────────────────────────────
                from dotenv import load_dotenv
                load_dotenv(_env_path(), override=True)

                # ── 2. Pre-flight: check required packages (dev mode only) ───
                # In a frozen/bundled app all packages are included — skip.
                if not _FROZEN:
                    missing = _check_required_packages()
                    if missing:
                        msg = f"Faltan los paquetes {', '.join(missing)}. Revisá la instalación."
                        _speak(msg)
                        self._notify(msg)
                        logger.error("[Tray] Paquetes faltantes: %s", missing)
                        return

                # ── 3. Wake word models ───────────────────────────────────────
                if not _has_wakeword_models():
                    _speak("Descargando los modelos de reconocimiento de voz. Esto solo ocurre una vez.")
                    self._notify("Descargando modelos de voz…")
                    logger.info("[Tray] Descargando modelos de wake word...")
                    try:
                        from openwakeword.utils import download_models
                        download_models()
                        _speak("Modelos instalados correctamente.")
                    except Exception as exc:
                        msg = "No pude descargar los modelos. Verificá tu conexión a internet."
                        _speak(msg)
                        self._notify(msg)
                        logger.warning("[Tray] Error descargando modelos: %s", exc)
                        return

                # ── 4. Microphone permission (macOS) ──────────────────────────
                if sys.platform == "darwin":
                    _request_mic_permission_macos()

                # ── 5. Start voice session ────────────────────────────────────
                _speak("Sistema listo. Decí Hey Jarvis para comenzar.")
                self._notify("Escuchando… Decí 'Hey Jarvis'")

                from core.server import jarvis_daemon
                jarvis_daemon.main()

            except ModuleNotFoundError as exc:
                msg = f"Falta el módulo {exc.name}. Reinstalá la aplicación."
                _speak(msg)
                self._notify(msg)
                logger.error("[Tray] Módulo faltante: %s", exc)
            except Exception as exc:
                msg = f"Ocurrió un error: {exc}"
                _speak(msg)
                self._notify(str(exc))
                logger.error("[Tray] Error en sesión: %s", exc)
            finally:
                self._running = False
                self._session = None
                if icon:
                    icon.icon = _load_icon_file(active=False)
                    icon.update_menu()

        self._thread = threading.Thread(target=_run, daemon=True, name="jarvis-session")
        self._thread.start()

    def stop_voice(self, icon: pystray.Icon, item: pystray.MenuItem) -> None:
        if not self._running:
            self._notify("J.A.R.V.I.S no está activo")
            return
        if self._session and hasattr(self._session, "stop"):
            self._session.stop()
        self._running = False
        self._notify("J.A.R.V.I.S detenido")
        icon.icon = _load_icon_file(active=False)
        icon.update_menu()

    # ── Auto-start toggle ─────────────────────────────────────────────────────

    def toggle_autostart(self, icon: pystray.Icon, item: pystray.MenuItem) -> None:
        if _is_autostart_enabled():
            _disable_autostart()
            self._notify("Auto-inicio desactivado")
        else:
            _enable_autostart()
            self._notify("J.A.R.V.I.S iniciará automáticamente con el sistema")
        icon.update_menu()

    # ── Config ────────────────────────────────────────────────────────────────

    def open_config(self, icon: pystray.Icon, item: pystray.MenuItem) -> None:
        import subprocess

        _ensure_env_exists()
        target = _env_path()

        # If the file still doesn't exist, create a minimal template
        if not os.path.exists(target):
            with open(target, "w") as f:
                f.write(
                    "# J.A.R.V.I.S — Configuración\n"
                    "# Sin API keys necesarias. Todo corre localmente.\n\n"
                    "OLLAMA_HOST=http://localhost:11434\n"
                    "JARVIS_GENERAL_MODEL=gemma4:latest\n"
                    "JARVIS_PC_MODEL=gemma4:latest\n"
                    "JARVIS_CODE_MODEL=qwen2.5-coder:latest\n"
                    "ACTIVE_TTS_ENGINE=edge_tts\n"
                    "ACTIVE_STT_ENGINE=mlx_whisper\n"
                )

        try:
            if sys.platform == "darwin":
                subprocess.Popen(["open", target])
            elif sys.platform == "win32":
                os.startfile(target)  # type: ignore[attr-defined]
            else:
                subprocess.Popen(["xdg-open", target])
        except Exception as exc:
            logger.error("[Tray] No se pudo abrir el archivo de config: %s", exc)
            self._notify(f"Config en: {target}")

    # ── Quit ──────────────────────────────────────────────────────────────────

    def quit(self, icon: pystray.Icon, item: pystray.MenuItem) -> None:
        self._running = False
        if self._session and hasattr(self._session, "stop"):
            self._session.stop()
        icon.stop()

    # ── Menu ──────────────────────────────────────────────────────────────────

    def open_panel(self, icon: pystray.Icon, item: pystray.MenuItem) -> None:
        if self._panel:
            self._panel.show()

    def build_menu(self) -> pystray.Menu:
        return pystray.Menu(
            pystray.MenuItem(
                "▶  Activar voz",
                self.start_voice,
                default=True,
                enabled=lambda _: not self._running,
            ),
            pystray.MenuItem(
                "⏹  Detener voz",
                self.stop_voice,
                enabled=lambda _: self._running,
            ),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("📊  Panel de control", self.open_panel),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem(
                "Iniciar con el sistema",
                self.toggle_autostart,
                checked=lambda _: _is_autostart_enabled(),
            ),
            pystray.MenuItem("⚙  Configuración (.env)", self.open_config),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("✕  Salir", self.quit),
        )


# ── Entry point ────────────────────────────────────────────────────────────────

def run_tray() -> None:
    """Launch J.A.R.V.I.S as a system tray application. No terminal needed."""
    # On first bundled run, copy .env template to the user config dir
    _ensure_env_exists()

    # Load .env from the correct location (user config dir when bundled, project root in dev)
    try:
        from dotenv import load_dotenv
        env = _env_path()
        if os.path.exists(env):
            load_dotenv(env)
    except ImportError:
        pass

    ctrl = _TrayController()
    icon = pystray.Icon(
        name="jarvis",
        icon=_load_icon_file(active=False),
        title="J.A.R.V.I.S — Voice Assistant",
        menu=ctrl.build_menu(),
    )
    ctrl._icon = icon

    # ── Panel de control ───────────────────────────────────────────────────────
    # Se crea ANTES del setup wizard para tener un único tk.Tk() en el proceso.
    # En macOS, crear dos tk.Tk() en el mismo proceso produce un crash silencioso.
    def _push_to_talk():
        try:
            from core.audio.vad_listener import active_listening_requested
            active_listening_requested.set()
        except Exception as exc:
            logger.warning("[Tray] push-to-talk error: %s", exc)

    from jarvis.control_panel import ControlPanel
    panel = ControlPanel(trigger_recording=_push_to_talk)
    ctrl._panel = panel

    # pystray corre en background — tkinter toma el hilo principal
    icon.run_detached()

    # Si es la primera ejecución, mostrar el wizard como Toplevel sobre el panel.
    # on_complete=panel.show lo muestra cuando el wizard termina.
    # Si no es primera vez, mostrar el panel directamente.
    from jarvis.setup_wizard import is_first_run, run_setup_wizard
    if is_first_run():
        run_setup_wizard(parent=panel.root, on_complete=panel.show)
    else:
        panel.show()

    panel.mainloop()   # Único mainloop — maneja tanto el wizard como el panel
    icon.stop()


if __name__ == "__main__":
    run_tray()
