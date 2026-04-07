"""
J.A.R.V.I.S. CLI — Entry point principal.
Subcomandos: start, doctor, config
"""
from __future__ import annotations

import os
import sys
import click

# Asegurar que el root del proyecto esté en el path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)


# ─── Helpers de output ────────────────────────────────────────────────────────

def _ok(msg: str) -> None:
    click.echo(click.style(f"  ✓ {msg}", fg="green"))


def _warn(msg: str) -> None:
    click.echo(click.style(f"  ⚠ {msg}", fg="yellow"))


def _fail(msg: str) -> None:
    click.echo(click.style(f"  ✗ {msg}", fg="red"))


def _header(msg: str) -> None:
    click.echo(click.style(f"\n{msg}", bold=True))


# ─── Validación de entorno ────────────────────────────────────────────────────

REQUIRED_VARS: dict[str, list[str]] = {
    "gemini":  ["GEMINI_API_KEY"],
    "claude":  ["ANTHROPIC_API_KEY"],
    "groq":    ["GROQ_API_KEY"],
}

OPTIONAL_VARS = {
    "OPENROUTER_API_KEY": "OpenRouter (backend alternativo)",
}


def _validate_env(backend: str) -> list[str]:
    """
    Valida las variables de entorno necesarias para el backend seleccionado.
    Retorna lista de errores. Lista vacía = todo OK.
    """
    errors: list[str] = []
    required = REQUIRED_VARS.get(backend, [])
    for var in required:
        if not os.getenv(var):
            errors.append(f"Falta la variable de entorno: {var}")
    return errors


def _load_dotenv() -> None:
    """Carga .env si existe, silenciosamente."""
    try:
        from dotenv import load_dotenv
        env_path = os.path.join(PROJECT_ROOT, ".env")
        if os.path.exists(env_path):
            load_dotenv(env_path)
    except ImportError:
        pass


# ─── Grupo principal ──────────────────────────────────────────────────────────

@click.group()
@click.version_option(version="0.1.0", prog_name="jarvis")
def main() -> None:
    """
    J.A.R.V.I.S. — Voice-First Programming CLI.

    \b
    Comandos principales:
      jarvis start    Inicia el sistema de voz
      jarvis doctor   Verifica el estado del sistema
      jarvis config   Muestra la configuración actual
    """
    pass


# ─── jarvis start ─────────────────────────────────────────────────────────────

@main.command()
@click.option(
    "--backend",
    type=click.Choice(["gemini", "claude", "groq"], case_sensitive=False),
    default=None,
    envvar="ACTIVE_BRAIN_ENGINE",
    show_envvar=True,
    help="Motor LLM a utilizar. Sobreescribe ACTIVE_BRAIN_ENGINE del .env.",
)
@click.option(
    "--mode",
    type=click.Choice(["daemon", "pty"], case_sensitive=False),
    default="daemon",
    show_default=True,
    help=(
        "Modo de operación: "
        "'daemon' usa el servidor TCP con hooks de Gemini CLI, "
        "'pty' wrappea el CLI directamente en la terminal actual."
    ),
)
def start(backend: str | None, mode: str) -> None:
    """Inicia J.A.R.V.I.S. con el backend y modo seleccionados."""
    _load_dotenv()

    # Determinar backend efectivo
    effective_backend = (backend or os.getenv("ACTIVE_BRAIN_ENGINE", "gemini")).lower()

    # Validar entorno ANTES de arrancar
    errors = _validate_env(effective_backend)
    if errors:
        click.echo(click.style("\n[J.A.R.V.I.S] Error de configuración:\n", fg="red", bold=True))
        for err in errors:
            _fail(err)
        click.echo(
            click.style(
                f"\nEditá el archivo .env y agregá la API key para el backend '{effective_backend}'.\n"
                f"Podés copiarte el template: cp .env.example .env\n",
                fg="yellow",
            )
        )
        sys.exit(1)

    # Inyectar backend en el entorno para que los módulos lo lean
    os.environ["ACTIVE_BRAIN_ENGINE"] = effective_backend

    # Descargar modelos si es la primera vez
    _ensure_models()

    click.echo(
        click.style(
            f"\n[J.A.R.V.I.S] Iniciando — backend: {effective_backend.upper()}, modo: {mode}\n",
            fg="cyan",
            bold=True,
        )
    )

    if mode == "pty":
        _start_pty()
    else:
        _start_daemon()


def _ensure_models() -> None:
    """
    Verifica que los modelos de wake word estén descargados.
    Si no están, los descarga automáticamente (solo ocurre la primera vez).
    """
    try:
        import openwakeword
        models_path = os.path.join(
            os.path.dirname(openwakeword.__file__), "resources", "models"
        )
        has_models = (
            os.path.isdir(models_path)
            and any(f.endswith(".onnx") for f in os.listdir(models_path))
        )
        if not has_models:
            click.echo(
                click.style(
                    "\n[J.A.R.V.I.S] Primera ejecución — descargando modelos de wake word...",
                    fg="yellow",
                )
            )
            from openwakeword.utils import download_models
            download_models()
            click.echo(click.style("  ✓ Modelos descargados correctamente.\n", fg="green"))
    except Exception as e:
        click.echo(click.style(f"\n  ⚠ No se pudieron descargar los modelos: {e}\n", fg="yellow"))


def _start_pty() -> None:
    """Inicia el modo PTY (wrappea el CLI en la terminal actual)."""
    try:
        import main as jarvis_main
        jarvis_main.main()
    except ImportError as e:
        _fail(f"No se pudo cargar el modo PTY: {e}")
        sys.exit(1)


def _start_daemon() -> None:
    """Inicia el modo Daemon (servidor TCP + hooks)."""
    try:
        from core.server import jarvis_daemon
        jarvis_daemon.main()
    except ImportError as e:
        _fail(f"No se pudo cargar el daemon: {e}")
        sys.exit(1)


# ─── jarvis doctor ────────────────────────────────────────────────────────────

@main.command()
@click.option(
    "--backend",
    type=click.Choice(["gemini", "claude", "groq"], case_sensitive=False),
    default=None,
    envvar="ACTIVE_BRAIN_ENGINE",
    help="Backend a verificar (por defecto usa ACTIVE_BRAIN_ENGINE o 'gemini').",
)
def doctor(backend: str | None) -> None:
    """Verifica que el entorno esté correctamente configurado."""
    _load_dotenv()
    effective_backend = (backend or os.getenv("ACTIVE_BRAIN_ENGINE", "gemini")).lower()

    click.echo(click.style("\n[J.A.R.V.I.S] Doctor — verificando el sistema...\n", bold=True))
    all_ok = True

    # ── Python ────────────────────────────────────────────────────────────────
    _header("Python")
    major, minor = sys.version_info[:2]
    if major >= 3 and minor >= 10:
        _ok(f"Python {major}.{minor} (mínimo requerido: 3.10)")
    else:
        _fail(f"Python {major}.{minor} — se requiere 3.10 o superior")
        all_ok = False

    # ── Variables de entorno ──────────────────────────────────────────────────
    _header(f"Variables de entorno (backend: {effective_backend.upper()})")
    env_errors = _validate_env(effective_backend)
    if env_errors:
        for err in env_errors:
            _fail(err)
        all_ok = False
    else:
        required = REQUIRED_VARS.get(effective_backend, [])
        for var in required:
            _ok(f"{var} ✓")

    for var, desc in OPTIONAL_VARS.items():
        if os.getenv(var):
            _ok(f"{var} ✓ ({desc})")
        else:
            _warn(f"{var} no configurado ({desc}) — opcional")

    # ── Dependencias de Python ────────────────────────────────────────────────
    _header("Dependencias de Python")

    deps_to_check = {
        "pyaudio":          "Audio I/O",
        "webrtcvad":        "Voice Activity Detection",
        "openwakeword":     "Wake word detection",
        "mlx_whisper":      "STT local (Apple Silicon)",
        "google.generativeai": "Gemini API",
        "groq":             "Groq API",
        "anthropic":        "Claude API",
        "dotenv":           "python-dotenv",
        "edge_tts":         "Edge TTS",
        "click":            "CLI framework",
    }

    for module, desc in deps_to_check.items():
        try:
            import warnings
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                __import__(module)
            _ok(f"{module} — {desc}")
        except ImportError:
            if module in ("anthropic",) and effective_backend != "claude":
                _warn(f"{module} no instalado — {desc} (no requerido para backend '{effective_backend}')")
            elif module in ("google.generativeai",) and effective_backend != "gemini":
                _warn(f"{module} no instalado — {desc} (no requerido para backend '{effective_backend}')")
            elif module in ("groq",) and effective_backend != "groq":
                _warn(f"{module} no instalado — {desc} (no requerido para backend '{effective_backend}')")
            else:
                _fail(f"{module} no instalado — {desc}")
                all_ok = False

    # ── Audio ─────────────────────────────────────────────────────────────────
    _header("Dispositivos de audio")
    try:
        import pyaudio
        pa = pyaudio.PyAudio()
        device_count = pa.get_device_count()
        input_devices = [
            pa.get_device_info_by_index(i)
            for i in range(device_count)
            if pa.get_device_info_by_index(i)["maxInputChannels"] > 0
        ]
        pa.terminate()
        if input_devices:
            _ok(f"{len(input_devices)} dispositivo(s) de entrada detectado(s)")
            for dev in input_devices[:3]:
                click.echo(f"     • {dev['name']}")
        else:
            _fail("No se detectó ningún micrófono")
            all_ok = False
    except Exception as e:
        _fail(f"Error al verificar audio: {e}")
        all_ok = False

    # ── Herramientas del sistema ───────────────────────────────────────────────
    _header("Herramientas del sistema")
    import shutil
    tools = {
        "ffmpeg":  "Reproducción de audio (Edge TTS)",
        "gemini":  "Gemini CLI (modo PTY/daemon)",
    }
    for tool, desc in tools.items():
        path = shutil.which(tool)
        if path:
            _ok(f"{tool} encontrado en {path} — {desc}")
        else:
            if tool == "gemini" and effective_backend != "gemini":
                _warn(f"{tool} no encontrado — {desc} (no requerido para backend '{effective_backend}')")
            else:
                _warn(f"{tool} no encontrado — {desc}")

    # ── Modelos locales ───────────────────────────────────────────────────────
    _header("Modelos locales")
    _check_wakeword_models()

    # ── Resultado final ───────────────────────────────────────────────────────
    click.echo()
    if all_ok:
        click.echo(click.style("✅  Sistema listo. Podés ejecutar: jarvis start\n", fg="green", bold=True))
    else:
        click.echo(
            click.style(
                "❌  Hay problemas que resolver. Revisá los errores de arriba.\n"
                "    Si es la primera vez, ejecutá: bash install.sh\n",
                fg="red",
                bold=True,
            )
        )
        sys.exit(1)


def _check_wakeword_models() -> None:
    """Verifica que los modelos de wake word estén descargados."""
    models_dir = os.path.expanduser("~/.jarvis/models")
    openwakeword_cache = os.path.join(
        os.path.expanduser("~"),
        "Library", "Caches", "openwakeword"
    )

    found_any = False
    for search_path in [models_dir, openwakeword_cache]:
        if os.path.isdir(search_path):
            model_files = [f for f in os.listdir(search_path) if f.endswith((".onnx", ".tflite"))]
            if model_files:
                _ok(f"Modelos wake word encontrados en {search_path} ({len(model_files)} archivos)")
                found_any = True
                break

    if not found_any:
        _warn("Modelos de wake word no encontrados — ejecutá: python download_models.py")


# ─── jarvis config ────────────────────────────────────────────────────────────

@main.command("config")
def show_config() -> None:
    """Muestra la configuración activa del sistema."""
    _load_dotenv()

    click.echo(click.style("\n[J.A.R.V.I.S] Configuración activa\n", bold=True))

    settings = {
        "Backend LLM":    os.getenv("ACTIVE_BRAIN_ENGINE", "gemini (default)"),
        "Motor TTS":      os.getenv("ACTIVE_TTS_ENGINE",   "mac_say (default)"),
        "Motor STT":      os.getenv("ACTIVE_STT_ENGINE",   "mlx_whisper (default)"),
        "Gemini API Key": "✓ configurada" if os.getenv("GEMINI_API_KEY") else "✗ no configurada",
        "Anthropic API":  "✓ configurada" if os.getenv("ANTHROPIC_API_KEY") else "✗ no configurada",
        "Groq API Key":   "✓ configurada" if os.getenv("GROQ_API_KEY") else "✗ no configurada",
        "Proyecto .env":  os.path.join(PROJECT_ROOT, ".env"),
    }

    max_len = max(len(k) for k in settings)
    for key, value in settings.items():
        color = "green" if "✓" in str(value) else ("red" if "✗" in str(value) else "white")
        click.echo(f"  {key:<{max_len}}  {click.style(str(value), fg=color)}")

    click.echo()
    click.echo(
        click.style(
            "Para cambiar la configuración, editá el archivo .env del proyecto.\n",
            fg="yellow",
        )
    )


if __name__ == "__main__":
    main()
