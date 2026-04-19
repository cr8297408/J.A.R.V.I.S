"""
FasterWhisperSTT — Cross-platform STT using faster-whisper.

Used on Windows, Linux, and Intel Macs where mlx-whisper is unavailable.
Automatically selects CUDA if available, otherwise CPU with int8 quantization.
"""
from __future__ import annotations

import logging

logger = logging.getLogger(__name__)

_TECH_PROMPT = (
    "Comandos de programación en terminal. "
    "Palabras clave: PR, Pull Request, issue, bug, branch, commit, "
    "merge, rebase, push, pull, fetch, clone, repo, proyecto, "
    "Python, JavaScript, React, Node, API, backend, frontend, "
    "script, archivo, carpeta, directorio, código, refactor, "
    "ticket, sprint, Jira, GitHub, GitLab, Claude, CLI, Jarvis. "
    "¿Cuántos PRs abiertos tiene el proyecto? "
    "Creame un nuevo issue para este bug."
)


class FasterWhisperSTT:
    """STT adapter using faster-whisper. Works on CPU (int8) and CUDA (float16)."""

    def __init__(self, model_name: str = "small") -> None:
        from faster_whisper import WhisperModel

        device = "cuda" if self._has_cuda() else "cpu"
        compute_type = "float16" if device == "cuda" else "int8"
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
            initial_prompt=_TECH_PROMPT,
            temperature=0.0,
        )
        return "".join(s.text for s in segments).strip()
