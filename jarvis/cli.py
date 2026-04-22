"""
J.A.R.V.I.S. CLI — Entry point principal.

Comandos:
    jarvis start [--mode code|daemon]  Inicia el sistema de voz
    jarvis doctor                      Verifica el estado del sistema
    jarvis config                      Muestra la configuración actual
    jarvis desktop                     Lanza como app de system tray

Modos de start:
    code   → OpenCode + Ollama (PTY). Para programar por voz. (default)
    daemon → Daemon completo: GENERAL + PC CONTROL + notificaciones.
"""
from __future__ import annotations

import os
import sys
import shutil
import click

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)


# ── Helpers de output ─────────────────────────────────────────────────────────

def _ok(msg: str)   -> None: click.echo(click.style(f"  ✓ {msg}", fg="green"))
def _warn(msg: str) -> None: click.echo(click.style(f"  ⚠ {msg}", fg="yellow"))
def _fail(msg: str) -> None: click.echo(click.style(f"  ✗ {msg}", fg="red"))
def _header(msg: str) -> None: click.echo(click.style(f"\n{msg}", bold=True))


def _load_dotenv() -> None:
    try:
        from dotenv import load_dotenv
        env_path = os.path.join(PROJECT_ROOT, ".env")
        if os.path.exists(env_path):
            load_dotenv(env_path)
    except ImportError:
        pass


# ── Grupo principal ───────────────────────────────────────────────────────────

@click.group()
@click.version_option(version="0.2.0", prog_name="jarvis")
def main() -> None:
    """
    J.A.R.V.I.S. — Asistente de voz 100% local con Gemma 4.

    \b
    Sin API keys. Sin internet. Sin costo.
    Todo corre en tu máquina vía Ollama.

    \b
    Comandos:
      jarvis start    Inicia el sistema de voz
      jarvis doctor   Verifica el estado del sistema
      jarvis config   Muestra la configuración actual
      jarvis desktop  Lanza como app de escritorio (system tray)
    """
    pass


# ── jarvis start ──────────────────────────────────────────────────────────────

@main.command()
@click.option(
    "--mode",
    type=click.Choice(["code", "daemon"], case_sensitive=False),
    default="code",
    show_default=True,
    help=(
        "code: OpenCode + Ollama via PTY — para programar por voz. "
        "daemon: servidor completo con GENERAL + PC CONTROL."
    ),
)
def start(mode: str) -> None:
    """Inicia J.A.R.V.I.S."""
    _load_dotenv()
    _ensure_models()
    _check_ollama_running()

    click.echo(click.style(
        f"\n[J.A.R.V.I.S] Iniciando — modo: {mode.upper()}\n",
        fg="cyan", bold=True,
    ))

    if mode == "code":
        _start_coding()
    else:
        _start_daemon()


def _start_coding() -> None:
    """Lanza OpenCodePtySession — modo coding con OpenCode + Ollama."""
    if not shutil.which("opencode"):
        _warn(
            "'opencode' no encontrado en el PATH.\n"
            "  Instalá con: brew install sst/tap/opencode\n"
            "  O descargá en: github.com/sst/opencode/releases"
        )
    try:
        from core.session.opencode_pty_session import OpenCodePtySession
        OpenCodePtySession().run()
    except ImportError as e:
        _fail(f"No se pudo cargar OpenCodePtySession: {e}")
        sys.exit(1)


def _start_daemon() -> None:
    """Lanza el daemon con GENERAL + PC CONTROL + notificaciones."""
    try:
        from core.server import jarvis_daemon
        jarvis_daemon.main()
    except ImportError as e:
        _fail(f"No se pudo cargar el daemon: {e}")
        sys.exit(1)


def _check_ollama_running() -> None:
    """Avisa si Ollama no está corriendo — no bloquea el inicio."""
    try:
        import urllib.request
        ollama_host = os.getenv("OLLAMA_HOST", "http://localhost:11434")
        urllib.request.urlopen(f"{ollama_host}/api/tags", timeout=2)
    except Exception:
        click.echo(click.style(
            "\n  ⚠ Ollama no parece estar corriendo. Inicialo con: ollama serve\n",
            fg="yellow",
        ))


# ── jarvis doctor ─────────────────────────────────────────────────────────────

@main.command()
def doctor() -> None:
    """Verifica que el entorno esté correctamente configurado."""
    _load_dotenv()
    click.echo(click.style("\n[J.A.R.V.I.S] Doctor — verificando el sistema...\n", bold=True))
    all_ok = True

    # ── Python ────────────────────────────────────────────────────────────────
    _header("Python")
    major, minor = sys.version_info[:2]
    if sys.version_info >= (3, 10):
        _ok(f"Python {major}.{minor}")
    else:
        _fail(f"Python {major}.{minor} — se requiere 3.10 o superior")
        all_ok = False

    # ── Ollama ────────────────────────────────────────────────────────────────
    _header("Ollama (LLM local)")
    ollama_host = os.getenv("OLLAMA_HOST", "http://localhost:11434")
    try:
        import urllib.request, json as _json
        with urllib.request.urlopen(f"{ollama_host}/api/tags", timeout=3) as resp:
            data = _json.loads(resp.read())
            models = [m["name"] for m in data.get("models", [])]
            _ok(f"Ollama corriendo en {ollama_host}")
            if models:
                _ok(f"Modelos disponibles: {', '.join(models[:5])}")
            else:
                _warn("No hay modelos descargados. Ejecutá: ollama pull gemma4")
                all_ok = False
    except Exception:
        _fail(f"Ollama no está corriendo en {ollama_host}")
        click.echo(click.style("     Inicialo con: ollama serve", fg="yellow"))
        all_ok = False

    # Verificar modelos específicos requeridos
    general_model = os.getenv("JARVIS_GENERAL_MODEL", "gemma4:latest")
    pc_model      = os.getenv("JARVIS_PC_MODEL",      "gemma4:latest")
    code_model    = os.getenv("JARVIS_CODE_MODEL",    "qwen2.5-coder:latest")
    for model_name, role in [(general_model, "GENERAL"), (pc_model, "PC"), (code_model, "CODING")]:
        try:
            import urllib.request, json as _json
            base = model_name.split(":")[0]
            with urllib.request.urlopen(f"{ollama_host}/api/tags", timeout=3) as resp:
                data = _json.loads(resp.read())
                installed = [m["name"] for m in data.get("models", [])]
                if any(base in m for m in installed):
                    _ok(f"Modelo {role}: {model_name}")
                else:
                    _warn(f"Modelo {role} no encontrado: {model_name} — ejecutá: ollama pull {base}")
        except Exception:
            _warn(f"No se pudo verificar el modelo {role}: {model_name}")

    # ── OpenCode ──────────────────────────────────────────────────────────────
    _header("OpenCode (agente de coding)")
    path = shutil.which("opencode")
    if path:
        _ok(f"opencode encontrado en {path}")
    else:
        _warn("opencode no encontrado — instalá con: brew install sst/tap/opencode")

    # ── Dependencias de Python ────────────────────────────────────────────────
    _header("Dependencias de Python")
    deps = {
        "pyaudio":      "Audio I/O",
        "webrtcvad":    "Voice Activity Detection",
        "openwakeword": "Wake word detection",
        "openai":       "Cliente HTTP para Ollama",
        "dotenv":       "python-dotenv",
        "edge_tts":     "Edge TTS",
        "click":        "CLI framework",
        "PIL":          "Pillow — screenshots",
        "pyautogui":    "Control de teclado/mouse",
    }
    for module, desc in deps.items():
        try:
            __import__(module)
            _ok(f"{module} — {desc}")
        except ImportError:
            _fail(f"{module} no instalado — {desc}")
            all_ok = False

    # Screen reader por plataforma
    _header("Screen Reader (Accessibility API)")
    if sys.platform == "darwin":
        try:
            import AppKit  # noqa: F401
            _ok("pyobjc-framework-Cocoa — NSAccessibility (macOS)")
        except ImportError:
            _warn("pyobjc no instalado — instalá: pip install pyobjc-framework-Cocoa pyobjc-framework-ApplicationServices")
    elif sys.platform == "win32":
        try:
            import pywinauto  # noqa: F401
            _ok("pywinauto — UI Automation (Windows)")
        except ImportError:
            _warn("pywinauto no instalado — instalá: pip install pywinauto")

    # ── Audio ─────────────────────────────────────────────────────────────────
    _header("Dispositivos de audio")
    try:
        import pyaudio
        pa = pyaudio.PyAudio()
        inputs = [
            pa.get_device_info_by_index(i)
            for i in range(pa.get_device_count())
            if pa.get_device_info_by_index(i)["maxInputChannels"] > 0
        ]
        pa.terminate()
        if inputs:
            _ok(f"{len(inputs)} micrófono(s) detectado(s)")
            for dev in inputs[:3]:
                click.echo(f"     • {dev['name']}")
        else:
            _fail("No se detectó ningún micrófono")
            all_ok = False
    except Exception as e:
        _fail(f"Error al verificar audio: {e}")
        all_ok = False

    # ── Modelos de wake word ──────────────────────────────────────────────────
    _header("Modelos de wake word")
    _check_wakeword_models()

    # ── Resultado ─────────────────────────────────────────────────────────────
    click.echo()
    if all_ok:
        click.echo(click.style("✅  Sistema listo. Ejecutá: jarvis start\n", fg="green", bold=True))
    else:
        click.echo(click.style(
            "❌  Hay problemas. Revisá los errores arriba.\n"
            "    Primera vez: bash install.sh\n",
            fg="red", bold=True,
        ))
        sys.exit(1)


# ── jarvis config ─────────────────────────────────────────────────────────────

@main.command("config")
def show_config() -> None:
    """Muestra la configuración activa del sistema."""
    _load_dotenv()
    click.echo(click.style("\n[J.A.R.V.I.S] Configuración activa\n", bold=True))

    settings = {
        "Ollama host":        os.getenv("OLLAMA_HOST",          "http://localhost:11434 (default)"),
        "Modelo GENERAL":     os.getenv("JARVIS_GENERAL_MODEL", "gemma4:latest (default)"),
        "Modelo PC CONTROL":  os.getenv("JARVIS_PC_MODEL",      "gemma4:latest (default)"),
        "Modelo CODING":      os.getenv("JARVIS_CODE_MODEL",    "qwen2.5-coder:latest (default)"),
        "Motor TTS":          os.getenv("ACTIVE_TTS_ENGINE",    "edge_tts (default)"),
        "Motor STT":          os.getenv("ACTIVE_STT_ENGINE",    "mlx_whisper (default)"),
        "Proyecto .env":      os.path.join(PROJECT_ROOT, ".env"),
    }

    max_len = max(len(k) for k in settings)
    for key, value in settings.items():
        click.echo(f"  {key:<{max_len}}  {click.style(str(value), fg='cyan')}")

    click.echo()
    click.echo(click.style(
        "Para cambiar la configuración, editá el archivo .env del proyecto.\n"
        "Template disponible en .env.example\n",
        fg="yellow",
    ))


# ── jarvis desktop ────────────────────────────────────────────────────────────

@main.command("desktop")
def desktop_mode() -> None:
    """
    Lanza J.A.R.V.I.S como app de escritorio (system tray).

    \b
    No requiere terminal. Ícono en la barra del sistema.
    Compatible con macOS, Windows y Linux.
    """
    try:
        from jarvis.tray import run_tray
    except ImportError as e:
        _fail(f"No se pudo cargar el modo desktop: {e}")
        click.echo(click.style(
            "\nInstalá las dependencias:\n  pip install pystray Pillow\n",
            fg="yellow",
        ))
        sys.exit(1)
    run_tray()


# ── Helpers ───────────────────────────────────────────────────────────────────

def _wakeword_model_dirs() -> list[str]:
    dirs: list[str] = []
    try:
        import openwakeword
        dirs.append(os.path.join(os.path.dirname(openwakeword.__file__), "resources", "models"))
    except Exception:
        pass
    home = os.path.expanduser("~")
    dirs.append(os.path.join(home, "Library", "Caches", "openwakeword"))
    dirs.append(os.path.join(os.getenv("XDG_CACHE_HOME", os.path.join(home, ".cache")), "openwakeword"))
    local_app = os.getenv("LOCALAPPDATA")
    if local_app:
        dirs.append(os.path.join(local_app, "openwakeword"))
    seen: set[str] = set()
    return [d for d in dirs if not (os.path.normpath(d) in seen or seen.add(os.path.normpath(d)))]  # type: ignore[arg-type]


def _has_wakeword_models() -> bool:
    for path in _wakeword_model_dirs():
        if os.path.isdir(path):
            try:
                if any(f.endswith(".onnx") for f in os.listdir(path)):
                    return True
            except OSError:
                continue
    return False


def _ensure_models() -> None:
    try:
        if _has_wakeword_models():
            return
        click.echo(click.style(
            "\n[J.A.R.V.I.S] Primera ejecución — descargando modelos de wake word...",
            fg="yellow",
        ))
        from openwakeword.utils import download_models
        download_models()
        if _has_wakeword_models():
            click.echo(click.style("  ✓ Modelos descargados correctamente.\n", fg="green"))
        else:
            _warn(f"Modelos no encontrados. Rutas buscadas: {_wakeword_model_dirs()}")
    except Exception as e:
        click.echo(click.style(f"\n  ⚠ No se pudieron descargar los modelos: {e}\n", fg="yellow"))


def _check_wakeword_models() -> None:
    for path in _wakeword_model_dirs():
        if os.path.isdir(path):
            try:
                models = [f for f in os.listdir(path) if f.endswith(".onnx")]
                if models:
                    _ok(f"{len(models)} modelo(s) en {path}")
                    return
            except OSError:
                continue
    _warn("Modelos no encontrados — se descargarán automáticamente al hacer 'jarvis start'")


if __name__ == "__main__":
    main()
