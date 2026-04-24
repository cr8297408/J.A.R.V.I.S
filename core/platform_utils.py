"""
Platform detection utilities for adapter auto-selection.

Import this module instead of importing platform-specific adapters directly.
All adapter selections respect the ACTIVE_STT_ENGINE / ACTIVE_TTS_ENGINE env vars,
falling back to the best available adapter for the current OS/hardware.
"""
from __future__ import annotations

import logging
import os
import platform
import sys

logger = logging.getLogger(__name__)


# ── Platform predicates ────────────────────────────────────────────────────────

def is_apple_silicon() -> bool:
    """True on macOS running on Apple Silicon (M1/M2/M3/M4)."""
    return sys.platform == "darwin" and platform.machine() == "arm64"


def is_macos() -> bool:
    return sys.platform == "darwin"


def is_windows() -> bool:
    return sys.platform == "win32"


def is_linux() -> bool:
    return sys.platform.startswith("linux")


# ── Adapter selection ──────────────────────────────────────────────────────────

def get_stt_class():
    """
    Returns the STT class best suited for the current platform.

    Selection order:
    1. ACTIVE_STT_ENGINE env var  (override explícito)
    2. apple_speech  — macOS, si pyobjc-framework-Speech está instalado
    3. mlx_whisper   — Apple Silicon, si apple_speech no está disponible
    4. faster_whisper — Windows / Linux (CPU int8 / CUDA float16)

    Valores válidos para ACTIVE_STT_ENGINE: apple_speech, mlx_whisper, faster_whisper
    """
    engine = _env("ACTIVE_STT_ENGINE")

    if engine == "mlx_whisper" or (not engine and is_apple_silicon()):
        from adapters.stt.mlx_stt import LocalSTT  # type: ignore[import]
        return LocalSTT

    from adapters.stt.faster_whisper_stt import FasterWhisperSTT
    return FasterWhisperSTT


def get_tts_class():
    """
    Returns the TTS class best suited for the current platform.

    Selection order:
    1. ACTIVE_TTS_ENGINE env var (explicit override)
    2. mac_say  — if macOS (zero latency, no network)
    3. edge_tts — everywhere else (neural voice, requires network)
    """
    engine = _env("ACTIVE_TTS_ENGINE")

    if engine == "mac_say" or (not engine and is_macos()):
        from adapters.tts.mac_say_tts import MacSayTTS  # type: ignore[import]
        return MacSayTTS

    from adapters.tts.edge_tts_adapter import EdgeTTS
    return EdgeTTS


# ── Audio playback ─────────────────────────────────────────────────────────────

def get_audio_player_cmd(file_path: str) -> list[str]:
    """
    Returns the shell command to play an audio file on the current platform.
    Prefers ffplay (cross-platform) then falls back to native players.
    """
    import shutil

    if is_macos():
        return ["afplay", file_path]

    if is_windows():
        # PowerShell MediaPlayer handles MP3 natively
        return [
            "powershell",
            "-c",
            f"(New-Object Media.SoundPlayer '{file_path}').PlaySync()",
        ]

    # Linux: ffplay > mpg123 > aplay (aplay is WAV-only, last resort)
    for player, args in [
        ("ffplay", ["-nodisp", "-autoexit", file_path]),
        ("mpg123", [file_path]),
        ("aplay", [file_path]),
    ]:
        if shutil.which(player):
            return [player] + (args[:-1] if player == "aplay" else args)

    raise RuntimeError(
        "No audio player found. Install ffmpeg: sudo apt-get install ffmpeg"
    )


# ── Helpers ────────────────────────────────────────────────────────────────────

def _env(key: str) -> str:
    return os.getenv(key, "").strip().lower()
