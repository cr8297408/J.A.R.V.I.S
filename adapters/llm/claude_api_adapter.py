"""
Claude API Adapter — streaming directo sin PTY.

Flujo: user_message → Claude API stream → StreamingLexer → (TEXT_CHUNK | CODE_BLOCK)
El llamador itera los yields y los pasa al TTS.
"""
from __future__ import annotations

import os
import logging
import anthropic

from core.lexer.poc_lexer import StreamingLexer

logger = logging.getLogger(__name__)

# Modelos disponibles: velocidad vs capacidad
MODELS = {
    "fast":     "claude-haiku-4-5-20251001",  # Clasificación, respuestas simples
    "smart":    "claude-sonnet-4-6",           # Coding, razonamiento (default)
    "powerful": "claude-opus-4-6",             # Tareas muy complejas
}

SYSTEM_PROMPT = """\
Eres J.A.R.V.I.S. (Just A Rather Very Intelligent System), un asistente de programación \
controlado 100% por voz.

REGLAS CRÍTICAS:
1. Respondés en el mismo idioma en que te hablan (español o inglés).
2. Tus respuestas son SIEMPRE cortas y directas — pensá en oraciones, no párrafos.
3. NUNCA leas código en voz alta. Si generás código, describí qué hace en una oración.
4. NUNCA leas rutas de archivo, URLs completas ni stack traces.
5. Si el usuario pide algo ambiguo, preguntá UNA sola cosa de aclaración.
6. Tratás al usuario como "Señor" cuando querés ser formal.
7. No usás emojis, markdown ni formato en tus respuestas — hablás como humano.

CONTEXTO:
Estás integrado en un CLI de terminal. El usuario habla y vos respondés por voz.
Podés ayudar con: código, git, búsquedas en el proyecto, explicaciones técnicas.
"""


class ClaudeAPIAdapter:
    """
    Adaptador de Claude API con streaming.

    Uso:
        adapter = ClaudeAPIAdapter()
        async for chunk_type, content in adapter.stream_response("creá un archivo hello.py"):
            if chunk_type == "TEXT_CHUNK":
                tts.speak(content)
            elif chunk_type == "CODE_BLOCK":
                summary = await summarizer.summarize(content)
                tts.speak(summary)
    """

    def __init__(self, model: str = "smart") -> None:
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("Falta la variable de entorno ANTHROPIC_API_KEY.")

        self.client = anthropic.AsyncAnthropic(api_key=api_key)
        self.model_name = MODELS.get(model, MODELS["smart"])
        self._history: list[dict] = []

        logger.info(f"Claude API Adapter listo — modelo: {self.model_name}")

    async def stream_response(self, user_message: str):
        """
        Envía un mensaje a Claude y hace streaming de la respuesta.

        Yields:
            ("TEXT_CHUNK", str)  — fragmento de texto listo para TTS
            ("CODE_BLOCK", str)  — bloque de código para resumir antes de hablar
        """
        self._history.append({"role": "user", "content": user_message})

        lexer = StreamingLexer()
        chunks: list[str] = []  # Fix #3: evitar O(n²) con concatenación de strings

        try:
            async with self.client.messages.stream(
                model=self.model_name,
                max_tokens=2048,
                system=SYSTEM_PROMPT,
                messages=self._history,
            ) as stream:
                async for text_chunk in stream.text_stream:
                    chunks.append(text_chunk)
                    chunk_type, content = await lexer.process_token(text_chunk)
                    if chunk_type is not None and content:
                        yield chunk_type, content

            # Fix #4: flush respetando el estado del lexer
            pending = lexer.buffer.strip()
            if pending:
                yield ("CODE_BLOCK" if lexer.in_code_block else "TEXT_CHUNK"), pending
                lexer.buffer = ""

        except anthropic.AuthenticationError:
            logger.error("Claude API: clave inválida o expirada.")
            self._history.pop()  # Fix #2: revertir user message huérfano
            yield "TEXT_CHUNK", "Señor, la clave de Anthropic no es válida."
            return
        except anthropic.RateLimitError:
            logger.error("Claude API: rate limit alcanzado.")
            self._history.pop()  # Fix #2
            yield "TEXT_CHUNK", "Señor, alcanzamos el límite de la API. Esperemos un momento."
            return
        except Exception as e:
            logger.error(f"Claude API error: {e}")
            self._history.pop()  # Fix #2
            yield "TEXT_CHUNK", "Señor, hubo un error al contactar a Claude."
            return

        # Guardar la respuesta completa en el historial para multi-turn
        full_response = "".join(chunks)
        if full_response:
            self._history.append({"role": "assistant", "content": full_response})
            self._maybe_compact_history()

    def _maybe_compact_history(self) -> None:
        """
        Mantiene el historial dentro de un límite razonable.
        Conserva siempre los últimos 20 turnos (40 mensajes).
        """
        MAX_MESSAGES = 40
        if len(self._history) > MAX_MESSAGES:
            self._history = self._history[-MAX_MESSAGES:]
            logger.info("Historial compactado — conservando últimos 20 turnos.")

    def abort_last_turn(self) -> None:
        """
        Descarta el turno incompleto cuando hay barge-in.
        Elimina el último mensaje del usuario si no tiene respuesta del assistant.
        """
        if self._history and self._history[-1]["role"] == "user":
            self._history.pop()
            logger.info("Turno abortado — mensaje del usuario revertido del historial.")

    def reset_history(self) -> None:
        """Limpia el historial de conversación (nueva sesión)."""
        self._history = []
        logger.info("Historial de conversación limpiado.")

    @property
    def turn_count(self) -> int:
        return len(self._history) // 2
