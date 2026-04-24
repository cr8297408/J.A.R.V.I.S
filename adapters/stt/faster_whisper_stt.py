"""
FasterWhisperSTT — Cross-platform STT using faster-whisper.

Used on Windows and Linux (and as fallback on macOS if SFSpeechRecognizer unavailable).
Auto-selects model and compute type based on available hardware:
  - CUDA  → medium + float16  (GPU acelerado)
  - CPU   → base   + int8     (liviano, razonable en CPU)
"""
from __future__ import annotations

import logging

logger = logging.getLogger(__name__)


class FasterWhisperSTT:
    """STT adapter using faster-whisper. Works on CPU (int8) and CUDA (float16)."""

    def __init__(self, model_name: str | None = None) -> None:
        from faster_whisper import WhisperModel

        device = "cuda" if self._has_cuda() else "cpu"
        compute_type = "float16" if device == "cuda" else "int8"

        # Modelo por defecto según hardware: medium en GPU, base en CPU.
        # base es mucho más liviano y suficiente para comandos cortos en CPU.
        if model_name is None:
            model_name = "medium" if device == "cuda" else "base"

        logger.info(
            "[FasterWhisperSTT] Cargando modelo '%s' en %s (%s)",
            model_name,
            device,
            compute_type,
        )
        self.model = WhisperModel(model_name, device=device, compute_type=compute_type)

    @staticmethod
    def _has_cuda() -> bool:
        try:
            import torch  # type: ignore[import]
            return bool(torch.cuda.is_available())
        except ImportError:
            return False

    def transcribe(self, audio_file_path: str) -> str:
        """Transcribe a WAV file and return the text."""
        segments, _ = self.model.transcribe(
            audio_file_path,
            language="es",
            temperature=0.0,
        )
        return "".join(s.text for s in segments).strip()
