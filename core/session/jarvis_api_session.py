"""
JarvisAPISession — Sesión en modo API (sin PTY).

Flujo completo:
    Wake word → Whisper STT → ClaudeAPIAdapter (streaming) → Lexer → TTS

Es el reemplazo del daemon para el backend 'claude'.
"""
from __future__ import annotations

import asyncio
import threading
import logging
import os

logger = logging.getLogger(__name__)


class JarvisAPISession:
    """
    Orquestador para el modo API.
    Conecta VAD → Claude → TTS sin ningún proceso PTY externo.
    """

    def __init__(self, model: str = "smart") -> None:
        from adapters.llm.claude_api_adapter import ClaudeAPIAdapter
        from adapters.tts.mac_say_tts import MacSayTTS

        self.claude = ClaudeAPIAdapter(model=model)
        self.tts = MacSayTTS()
        self.interrupt_event = threading.Event()
        self._loop: asyncio.AbstractEventLoop | None = None

    # ── Punto de entrada ──────────────────────────────────────────────────────

    def run(self) -> None:
        """Inicia la sesión. Bloqueante hasta Ctrl+C."""
        print("\r\n[J.A.R.V.I.S] Modo API — Claude directo. Di 'Hey Jarvis' para empezar.\r\n")

        self._loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._loop)

        # Arrancar el VAD en un hilo demonio con nuestro callback
        from core.audio.vad_listener import start_vad_thread
        start_vad_thread(
            interrupt_event=self.interrupt_event,
            on_transcription=self._on_user_speech,
            loop=self._loop,
        )

        try:
            self._loop.run_forever()
        except KeyboardInterrupt:
            logger.info("Sesión API terminada por el usuario.")
        finally:
            self._loop.close()

    # ── Callback de transcripción ─────────────────────────────────────────────

    def _on_user_speech(self, text: str) -> None:
        """
        Llamado desde el hilo del VAD cuando el usuario termina de hablar.
        Despacha el mensaje a Claude en el event loop principal.
        """
        if not self._loop:
            return
        asyncio.run_coroutine_threadsafe(
            self._process_message(text),
            self._loop,
        )

    # ── Pipeline principal ────────────────────────────────────────────────────

    async def _process_message(self, user_message: str) -> None:
        """
        Envía el mensaje a Claude y habla la respuesta en streaming.
        Barge-in: si interrupt_event se activa, para de hablar.
        """
        logger.info(f"Mensaje del usuario: {user_message}")

        # Limpiar el evento por si quedó de una interrupción anterior
        self.interrupt_event.clear()

        async for chunk_type, content in self.claude.stream_response(user_message):
            # Si el usuario interrumpió mientras Claude generaba, cortamos
            if self.interrupt_event.is_set():
                logger.info("Barge-in durante generación — cortando respuesta.")
                self.claude.abort_last_turn()  # Fix #1: API pública, revierte solo si el turno quedó huérfano
                break

            if chunk_type == "TEXT_CHUNK":
                await asyncio.to_thread(self.tts.speak, content, self.interrupt_event)

            elif chunk_type == "CODE_BLOCK":
                # Por ahora resumimos el bloque con una descripción genérica.
                # Issue #7 (FileReadTool) y #25 (Smart Summarizer) lo mejoran.
                summary = f"Acá generé un bloque de código con {len(content.splitlines())} líneas."
                await asyncio.to_thread(self.tts.speak, summary, self.interrupt_event)
