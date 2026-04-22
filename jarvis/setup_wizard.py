"""
J.A.R.V.I.S. — First-Run Setup Wizard.

Ventana tkinter que aparece la primera vez que se abre la app.
Guía al usuario a través de la instalación de:
  1. Ollama (servidor LLM local)
  2. Modelos Gemma 4 + Qwen Coder
  3. OpenCode (agente de coding)
  4. Dependencias Python del audio pipeline

No requiere conocimiento técnico. Un solo botón "Instalar todo".
"""
from __future__ import annotations

import os
import sys
import subprocess
import threading
import urllib.request
import json
import shutil
import logging

logger = logging.getLogger(__name__)

# ── Sentinel de primera ejecución ─────────────────────────────────────────────

def _config_dir() -> str:
    if sys.platform == "darwin":
        d = os.path.expanduser("~/Library/Application Support/JARVIS")
    elif sys.platform == "win32":
        d = os.path.join(os.getenv("APPDATA", os.path.expanduser("~")), "JARVIS")
    else:
        d = os.path.expanduser("~/.config/jarvis")
    os.makedirs(d, exist_ok=True)
    return d


def _setup_done_flag() -> str:
    return os.path.join(_config_dir(), ".setup_done")


def is_first_run() -> bool:
    return not os.path.exists(_setup_done_flag())


def mark_setup_done() -> None:
    with open(_setup_done_flag(), "w") as f:
        f.write("1")


# ── Chequeos del sistema ───────────────────────────────────────────────────────

def _ollama_installed() -> bool:
    return shutil.which("ollama") is not None


def _ollama_running() -> bool:
    try:
        with urllib.request.urlopen("http://localhost:11434/api/tags", timeout=2) as r:
            return r.status == 200
    except Exception:
        return False


def _models_installed() -> tuple[bool, bool]:
    """Returns (gemma4_ok, qwen_ok)."""
    try:
        with urllib.request.urlopen("http://localhost:11434/api/tags", timeout=3) as r:
            data = json.loads(r.read())
            names = [m["name"] for m in data.get("models", [])]
            gemma4 = any("gemma4" in n for n in names)
            qwen   = any("qwen2.5-coder" in n for n in names)
            return gemma4, qwen
    except Exception:
        return False, False


def _opencode_installed() -> bool:
    return shutil.which("opencode") is not None


def _python_deps_ok() -> bool:
    for mod in ("pyaudio", "webrtcvad", "openwakeword", "numpy"):
        try:
            __import__(mod)
        except ImportError:
            return False
    return True


# ── Instaladores ──────────────────────────────────────────────────────────────

def _install_ollama(log_fn) -> bool:
    """Instala Ollama. Devuelve True si tuvo éxito."""
    log_fn("Descargando instalador de Ollama...")
    try:
        if sys.platform == "darwin":
            log_fn("Instalando Ollama via script oficial...")
            r = subprocess.run(
                ["bash", "-c", "curl -fsSL https://ollama.com/install.sh | sh"],
                capture_output=True, text=True
            )
            if r.returncode == 0:
                log_fn("✓ Ollama instalado")
                return True
            log_fn(f"✗ Error: {r.stderr[-200:]}")
            return False

        elif sys.platform == "win32":
            log_fn("Instalando Ollama via PowerShell...")
            r = subprocess.run(
                ["powershell", "-Command", "irm https://ollama.com/install.ps1 | iex"],
                capture_output=True, text=True
            )
            if r.returncode == 0:
                log_fn("✓ Ollama instalado")
                return True
            log_fn(f"✗ Error: {r.stderr[-200:]}")
            return False

        else:  # Linux
            log_fn("Instalando Ollama via script oficial...")
            r = subprocess.run(
                ["bash", "-c", "curl -fsSL https://ollama.com/install.sh | sh"],
                capture_output=True, text=True
            )
            if r.returncode == 0:
                log_fn("✓ Ollama instalado")
                return True
            log_fn(f"✗ Error: {r.stderr[-200:]}")
            return False

    except Exception as e:
        log_fn(f"✗ Error instalando Ollama: {e}")
        return False


def _start_ollama_server(log_fn) -> bool:
    """Inicia ollama serve en background. Devuelve True si levantó."""
    if _ollama_running():
        log_fn("✓ Ollama ya está corriendo")
        return True
    log_fn("Iniciando servidor Ollama...")
    try:
        subprocess.Popen(
            ["ollama", "serve"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        import time
        for _ in range(10):
            time.sleep(1)
            if _ollama_running():
                log_fn("✓ Servidor Ollama activo")
                return True
        log_fn("⚠ Ollama tardó en iniciar — reintentá en un momento")
        return False
    except Exception as e:
        log_fn(f"✗ No se pudo iniciar Ollama: {e}")
        return False


def _pull_model(model: str, log_fn) -> bool:
    """Descarga un modelo via ollama pull con output en tiempo real."""
    log_fn(f"Descargando {model}...")
    try:
        proc = subprocess.Popen(
            ["ollama", "pull", model],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )
        last_line = ""
        for line in proc.stdout:
            line = line.strip()
            if line and line != last_line:
                # Solo loguear cambios de porcentaje o mensajes importantes
                if "%" in line or any(k in line.lower() for k in ("pull", "manifest", "verif", "success", "error")):
                    log_fn(f"  {line}")
                    last_line = line
        proc.wait()
        if proc.returncode == 0:
            log_fn(f"✓ {model} descargado")
            return True
        else:
            log_fn(f"✗ Error descargando {model}")
            return False
    except Exception as e:
        log_fn(f"✗ {e}")
        return False


def _install_opencode(log_fn) -> bool:
    """Instala OpenCode."""
    log_fn("Instalando OpenCode...")
    try:
        if sys.platform == "darwin" and shutil.which("brew"):
            r = subprocess.run(
                ["brew", "install", "sst/tap/opencode"],
                capture_output=True, text=True
            )
            if r.returncode == 0:
                log_fn("✓ OpenCode instalado via Homebrew")
                return True

        # Fallback: binario desde GitHub releases
        import platform as _plat
        arch = _plat.machine().lower()
        if sys.platform == "darwin":
            plat_str = "darwin_arm64" if arch in ("arm64", "aarch64") else "darwin_amd64"
        elif sys.platform == "win32":
            plat_str = "windows_amd64"
        else:
            plat_str = "linux_amd64"

        log_fn("Obteniendo última versión de OpenCode...")
        try:
            with urllib.request.urlopen(
                "https://api.github.com/repos/sst/opencode/releases/latest",
                timeout=10
            ) as resp:
                release = json.loads(resp.read())
                tag = release.get("tag_name", "v0.1.0")
        except Exception:
            tag = "v0.1.0"

        url = f"https://github.com/sst/opencode/releases/download/{tag}/opencode_{plat_str}.tar.gz"
        tmp = f"/tmp/opencode_{plat_str}.tar.gz"
        log_fn(f"Descargando opencode {tag}...")
        urllib.request.urlretrieve(url, tmp)

        dest = "/usr/local/bin" if sys.platform != "win32" else os.path.join(os.environ.get("LOCALAPPDATA", ""), "Programs", "opencode")
        os.makedirs(dest, exist_ok=True)
        subprocess.run(["tar", "-xzf", tmp, "-C", dest], check=True)

        bin_path = os.path.join(dest, "opencode")
        if os.path.exists(bin_path):
            os.chmod(bin_path, 0o755)
            log_fn("✓ OpenCode instalado")
            return True
        return False

    except Exception as e:
        log_fn(f"✗ Error instalando OpenCode: {e}")
        return False


def _install_python_deps(log_fn) -> bool:
    """Instala las dependencias Python del audio pipeline."""
    log_fn("Instalando dependencias de audio (pyaudio, webrtcvad, openwakeword)...")
    try:
        pkgs = ["pyaudio", "webrtcvad", "openwakeword", "numpy", "python-dotenv", "edge-tts"]
        r = subprocess.run(
            [sys.executable, "-m", "pip", "install", "--quiet", *pkgs],
            capture_output=True, text=True
        )
        if r.returncode == 0:
            log_fn("✓ Dependencias Python instaladas")
            return True
        log_fn(f"✗ pip falló: {r.stderr[-300:]}")
        return False
    except Exception as e:
        log_fn(f"✗ {e}")
        return False


# ── GUI ───────────────────────────────────────────────────────────────────────

def run_setup_wizard(on_complete=None) -> None:
    """
    Muestra la ventana de setup. Bloquea hasta que el usuario completa o cierra.
    on_complete se llama sin argumentos cuando el setup termina exitosamente.
    """
    try:
        import tkinter as tk
        from tkinter import ttk
    except ImportError:
        # Sin GUI — correr en modo texto en la terminal
        _run_headless_setup()
        if on_complete:
            on_complete()
        return

    root = tk.Tk()
    root.title("J.A.R.V.I.S — Configuración inicial")
    root.resizable(False, False)
    root.configure(bg="#0a0a1a")

    # Centrar la ventana
    root.update_idletasks()
    w, h = 540, 560
    x = (root.winfo_screenwidth()  - w) // 2
    y = (root.winfo_screenheight() - h) // 2
    root.geometry(f"{w}x{h}+{x}+{y}")

    # ── Colores ───────────────────────────────────────────────────────────────
    BG      = "#0a0a1a"
    CARD_BG = "#12122a"
    BLUE    = "#0078d4"
    GREEN   = "#00c853"
    YELLOW  = "#ffd740"
    RED     = "#ff5252"
    WHITE   = "#e8e8ff"
    GRAY    = "#6666aa"

    # ── Header ────────────────────────────────────────────────────────────────
    header = tk.Frame(root, bg=BG)
    header.pack(fill="x", padx=24, pady=(20, 0))

    tk.Label(
        header, text="J.A.R.V.I.S",
        font=("SF Pro Display", 22, "bold") if sys.platform == "darwin" else ("Segoe UI", 22, "bold"),
        bg=BG, fg=BLUE,
    ).pack(anchor="w")

    tk.Label(
        header, text="Configuración inicial — 100% local, sin API keys, sin costo",
        font=("SF Pro Text", 11) if sys.platform == "darwin" else ("Segoe UI", 11),
        bg=BG, fg=GRAY,
    ).pack(anchor="w", pady=(2, 0))

    # ── Separador ─────────────────────────────────────────────────────────────
    tk.Frame(root, bg=BLUE, height=1).pack(fill="x", padx=24, pady=(12, 0))

    # ── Steps ─────────────────────────────────────────────────────────────────
    steps_frame = tk.Frame(root, bg=BG)
    steps_frame.pack(fill="x", padx=24, pady=(16, 0))

    STEPS = [
        ("ollama",     "Ollama",           "Servidor LLM local — corre Gemma 4 en tu máquina"),
        ("gemma4",     "Gemma 4",          "Modelo de lenguaje para conversación y control de PC"),
        ("qwen",       "Qwen 2.5 Coder",   "Modelo especializado en código (modo coding)"),
        ("opencode",   "OpenCode",         "Agente de coding open-source (reemplaza Claude Code)"),
        ("deps",       "Audio pipeline",   "pyaudio, webrtcvad, openwakeword"),
    ]

    step_icons: dict[str, tk.Label]  = {}
    step_labels: dict[str, tk.Label] = {}

    for key, name, desc in STEPS:
        row = tk.Frame(steps_frame, bg=CARD_BG, pady=8, padx=12)
        row.pack(fill="x", pady=3)

        icon = tk.Label(row, text="○", font=("Courier", 14), bg=CARD_BG, fg=GRAY, width=2)
        icon.pack(side="left", padx=(0, 10))
        step_icons[key] = icon

        info = tk.Frame(row, bg=CARD_BG)
        info.pack(side="left", fill="x", expand=True)

        tk.Label(info, text=name, font=(("SF Pro Text" if sys.platform=="darwin" else "Segoe UI"), 12, "bold"),
                 bg=CARD_BG, fg=WHITE, anchor="w").pack(fill="x")
        lbl = tk.Label(info, text=desc, font=(("SF Pro Text" if sys.platform=="darwin" else "Segoe UI"), 10),
                       bg=CARD_BG, fg=GRAY, anchor="w")
        lbl.pack(fill="x")
        step_labels[key] = lbl

    # ── Log ───────────────────────────────────────────────────────────────────
    log_frame = tk.Frame(root, bg=BG)
    log_frame.pack(fill="x", padx=24, pady=(14, 0))

    log_text = tk.Text(
        log_frame, height=5, bg="#060614", fg=GREEN,
        font=("Courier New", 9) if sys.platform == "win32" else ("Menlo", 9),
        relief="flat", state="disabled", wrap="word", bd=0,
        insertbackground=GREEN,
    )
    log_text.pack(fill="x")

    scrollbar = ttk.Scrollbar(log_frame, orient="vertical", command=log_text.yview)
    log_text.configure(yscrollcommand=scrollbar.set)

    # ── Progress bar ──────────────────────────────────────────────────────────
    progress_var = tk.DoubleVar(value=0)
    progress_bar = ttk.Progressbar(root, variable=progress_var, maximum=100, length=490)

    style = ttk.Style()
    style.theme_use("default")
    style.configure("TProgressbar", troughcolor="#12122a", background=BLUE, thickness=6)

    progress_bar.pack(padx=24, pady=(10, 0))

    # ── Botón principal ────────────────────────────────────────────────────────
    btn_frame = tk.Frame(root, bg=BG)
    btn_frame.pack(pady=(12, 20))

    install_btn = tk.Button(
        btn_frame, text="  Instalar todo  ",
        font=(("SF Pro Text" if sys.platform=="darwin" else "Segoe UI"), 13, "bold"),
        bg=BLUE, fg="white", relief="flat", padx=20, pady=8,
        cursor="hand2", activebackground="#005fa3", activeforeground="white",
    )
    install_btn.pack()

    skip_lbl = tk.Label(
        btn_frame, text="Omitir (ya tengo todo instalado)",
        font=(("SF Pro Text" if sys.platform=="darwin" else "Segoe UI"), 10),
        bg=BG, fg=GRAY, cursor="hand2",
    )
    skip_lbl.pack(pady=(8, 0))

    # ── Helpers de UI ─────────────────────────────────────────────────────────

    def log(msg: str) -> None:
        def _do():
            log_text.configure(state="normal")
            log_text.insert("end", msg + "\n")
            log_text.see("end")
            log_text.configure(state="disabled")
        root.after(0, _do)

    def set_step(key: str, state: str) -> None:
        """state: pending | running | ok | warn | error"""
        icons = {"pending": ("○", GRAY), "running": ("◉", BLUE),
                 "ok": ("✓", GREEN), "warn": ("⚠", YELLOW), "error": ("✗", RED)}
        symbol, color = icons.get(state, ("○", GRAY))
        def _do():
            step_icons[key].configure(text=symbol, fg=color)
        root.after(0, _do)

    def set_progress(pct: float) -> None:
        root.after(0, lambda: progress_var.set(pct))

    # ── Instalación en background ──────────────────────────────────────────────

    def _run_install():
        install_btn.configure(state="disabled", text="  Instalando…  ")
        skip_lbl.configure(fg="#333366")
        total = len(STEPS)
        done  = 0

        # 1. Ollama
        set_step("ollama", "running")
        log("── Verificando Ollama ──")
        if _ollama_installed():
            log("✓ Ollama ya instalado")
            set_step("ollama", "ok")
        else:
            ok = _install_ollama(log)
            set_step("ollama", "ok" if ok else "error")
        done += 1; set_progress(done / total * 80)

        # Iniciar servidor
        _start_ollama_server(log)

        # 2. Gemma 4
        set_step("gemma4", "running")
        log("── Verificando Gemma 4 ──")
        gemma4_ok, qwen_ok = _models_installed()
        if gemma4_ok:
            log("✓ gemma4:latest ya descargado")
            set_step("gemma4", "ok")
        else:
            ok = _pull_model("gemma4:latest", log)
            set_step("gemma4", "ok" if ok else "warn")
        done += 1; set_progress(done / total * 80)

        # 3. Qwen Coder
        set_step("qwen", "running")
        log("── Verificando Qwen 2.5 Coder ──")
        if qwen_ok:
            log("✓ qwen2.5-coder:latest ya descargado")
            set_step("qwen", "ok")
        else:
            ok = _pull_model("qwen2.5-coder:latest", log)
            set_step("qwen", "ok" if ok else "warn")
        done += 1; set_progress(done / total * 80)

        # 4. OpenCode
        set_step("opencode", "running")
        log("── Verificando OpenCode ──")
        if _opencode_installed():
            log("✓ OpenCode ya instalado")
            set_step("opencode", "ok")
        else:
            ok = _install_opencode(log)
            set_step("opencode", "ok" if ok else "warn")
        done += 1; set_progress(done / total * 80)

        # 5. Deps Python
        set_step("deps", "running")
        log("── Verificando dependencias Python ──")
        if _python_deps_ok():
            log("✓ Dependencias ya instaladas")
            set_step("deps", "ok")
        else:
            ok = _install_python_deps(log)
            set_step("deps", "ok" if ok else "error")
        done += 1; set_progress(100)

        log("\n✓ Configuración completa. ¡Listo para usar!")
        mark_setup_done()

        def _finish():
            install_btn.configure(
                text="  Iniciar J.A.R.V.I.S  ",
                state="normal",
                bg=GREEN,
                activebackground="#009624",
                command=_close_and_launch,
            )
        root.after(0, _finish)

    def _close_and_launch():
        root.destroy()
        if on_complete:
            on_complete()

    def _start_install():
        t = threading.Thread(target=_run_install, daemon=True)
        t.start()

    def _skip():
        mark_setup_done()
        root.destroy()
        if on_complete:
            on_complete()

    # Detectar estado inicial y pre-marcar lo que ya está ok
    def _precheck():
        if _ollama_installed(): set_step("ollama", "ok")
        gemma4_ok, qwen_ok = _models_installed()
        if gemma4_ok: set_step("gemma4", "ok")
        if qwen_ok:   set_step("qwen", "ok")
        if _opencode_installed(): set_step("opencode", "ok")
        if _python_deps_ok(): set_step("deps", "ok")

    install_btn.configure(command=_start_install)
    skip_lbl.bind("<Button-1>", lambda _: _skip())

    root.after(100, _precheck)
    root.mainloop()


def _run_headless_setup() -> None:
    """Fallback sin GUI — imprime en consola."""
    print("\n[J.A.R.V.I.S] Configuración inicial (modo texto)\n")

    def log(msg):
        print(f"  {msg}")

    if not _ollama_installed():
        _install_ollama(log)
    _start_ollama_server(log)

    g, q = _models_installed()
    if not g:
        _pull_model("gemma4:latest", log)
    if not q:
        _pull_model("qwen2.5-coder:latest", log)
    if not _opencode_installed():
        _install_opencode(log)
    if not _python_deps_ok():
        _install_python_deps(log)

    mark_setup_done()
    print("\n✓ Configuración completa.\n")


if __name__ == "__main__":
    run_setup_wizard()
