# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec for J.A.R.V.I.S Desktop App.

Generates:
  macOS  → J.A.R.V.I.S.app  (no dock icon, lives in system tray)
  Windows → JARVIS.exe       (single file, no console window)
  Linux  → jarvis-desktop    (single ELF binary)

Build command (from project root):
    python scripts/generate_icon.py   # generate icons first
    pyinstaller jarvis.spec

Output: dist/
"""
import os
import platform
import sys

_IS_MAC = sys.platform == "darwin"
_IS_WIN = sys.platform == "win32"
_IS_LINUX = sys.platform.startswith("linux")
_IS_APPLE_SILICON = _IS_MAC and platform.machine() == "arm64"


# ── Hidden imports ─────────────────────────────────────────────────────────────

hidden = [
    # Tray backends — pystray selects the right one at runtime
    "pystray._darwin",
    "pystray._win32",
    "pystray._xorg",
    # Core modules
    "jarvis.tray",
    "jarvis.cli",
    "core.platform_utils",
    "core.session.jarvis_api_session",
    "core.audio.vad_listener",
    "core.input.hotkey_listener",
    "core.server.jarvis_daemon",
    # Adapters
    "adapters.llm.claude_api_adapter",
    "adapters.llm.gemini_summarizer",
    "adapters.llm.groq_summarizer",
    "adapters.llm.openrouter_summarizer",
    "adapters.tts.mac_say_tts",
    "adapters.tts.edge_tts_adapter",
    "adapters.stt.ghost_typer",
    # Third-party — LLM backends (all must be bundled regardless of active engine)
    "anthropic",
    "groq",
    "google.generativeai",
    "openai",
    "click",
    "pynput",
    "pynput.keyboard._darwin",
    "pynput.keyboard._win32",
    "pynput.keyboard._xorg",
    "pynput.mouse._darwin",
    "pynput.mouse._win32",
    "pynput.mouse._xorg",
    "openwakeword",
    "openwakeword.utils",
    "openwakeword.model",
    "onnxruntime",
    "onnxruntime.capi._pybind_state",
    "webrtcvad",
    "numpy",
    "edge_tts",
    "PIL",
    "PIL.Image",
    "PIL.ImageDraw",
]

# Platform-specific STT
if _IS_APPLE_SILICON:
    hidden += ["adapters.stt.mlx_stt", "mlx_whisper"]
else:
    hidden += ["adapters.stt.faster_whisper_stt", "faster_whisper"]


# ── Data files ─────────────────────────────────────────────────────────────────

_assets = os.path.join("jarvis", "assets")
datas = []
if os.path.isdir(_assets):
    datas.append((_assets, os.path.join("jarvis", "assets")))

_env_example = ".env.example"
if os.path.exists(_env_example):
    datas.append((_env_example, "."))

# Bundle openwakeword models (.onnx) so the app works offline on first launch
try:
    import openwakeword as _oww
    _oww_resources = os.path.join(os.path.dirname(_oww.__file__), "resources")
    if os.path.isdir(_oww_resources):
        datas.append((_oww_resources, os.path.join("openwakeword", "resources")))
        print(f"[spec] Bundling openwakeword resources from {_oww_resources}")
    else:
        print("[spec] WARNING: openwakeword resources dir not found — models won't be bundled")
except ImportError:
    print("[spec] WARNING: openwakeword not installed — skipping model bundling")


# ── Icon paths ─────────────────────────────────────────────────────────────────

_icon_icns = os.path.join("jarvis", "assets", "icon.icns")
_icon_ico = os.path.join("jarvis", "assets", "icon.ico")
_icon_png = os.path.join("jarvis", "assets", "icon.png")

mac_icon = _icon_icns if os.path.exists(_icon_icns) else None
win_icon = _icon_ico if os.path.exists(_icon_ico) else None
lin_icon = _icon_png if os.path.exists(_icon_png) else None


# ── Analysis ───────────────────────────────────────────────────────────────────

block_cipher = None

a = Analysis(
    [os.path.join("jarvis", "tray.py")],
    pathex=["."],
    binaries=[],
    datas=datas,
    hiddenimports=hidden,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["matplotlib", "tkinter", "PyQt5", "PyQt6", "wx", "unittest"],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)


# ── Platform builds ────────────────────────────────────────────────────────────

if _IS_MAC:
    exe = EXE(
        pyz,
        a.scripts,
        [],
        exclude_binaries=True,
        name="jarvis-desktop",
        debug=False,
        bootloader_ignore_signals=False,
        strip=False,
        upx=False,
        console=False,
        icon=mac_icon,
    )
    coll = COLLECT(
        exe,
        a.binaries,
        a.zipfiles,
        a.datas,
        strip=False,
        upx=False,
        name="jarvis-desktop",
    )
    app = BUNDLE(  # noqa: F821 — defined by PyInstaller runtime
        coll,
        name="J.A.R.V.I.S.app",
        icon=mac_icon,
        bundle_identifier="com.jarvis.voice",
        info_plist={
            # Accessibility: no dock icon — lives only in the menu bar
            "LSUIElement": True,
            "NSHighResolutionCapable": True,
            "NSMicrophoneUsageDescription": (
                "J.A.R.V.I.S necesita acceso al micrófono "
                "para el reconocimiento de voz por comandos."
            ),
            "CFBundleDisplayName": "J.A.R.V.I.S",
            "CFBundleVersion": "0.1.0",
            "CFBundleShortVersionString": "0.1.0",
        },
    )

elif _IS_WIN:
    exe = EXE(
        pyz,
        a.scripts,
        a.binaries,
        a.zipfiles,
        a.datas,
        [],
        name="JARVIS",
        debug=False,
        bootloader_ignore_signals=False,
        strip=False,
        upx=True,
        upx_exclude=[],
        runtime_tmpdir=None,
        console=False,          # No cmd window
        disable_windowed_traceback=False,
        argv_emulation=False,
        icon=win_icon,
    )

else:  # Linux
    exe = EXE(
        pyz,
        a.scripts,
        a.binaries,
        a.zipfiles,
        a.datas,
        [],
        name="jarvis-desktop",
        debug=False,
        bootloader_ignore_signals=False,
        strip=True,
        upx=True,
        upx_exclude=[],
        runtime_tmpdir=None,
        console=False,
        argv_emulation=False,
        icon=lin_icon,
    )
