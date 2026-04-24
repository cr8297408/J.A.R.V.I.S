"""
OllamaAdapter — cerebro de Jarvis 100% local vía Ollama.

Reemplaza: GeminiSummarizer, GroqSummarizer, OpenRouterSummarizer, ClaudeAPIAdapter.
Sin API keys. Sin internet. Sin costo.

Ollama expone una API compatible con OpenAI en localhost:11434/v1,
por eso el cliente AsyncOpenAI funciona apuntando a esa URL.

Tres instancias recomendadas:
    brain_general = OllamaAdapter(model=GENERAL_MODEL)   # conversación libre
    brain_pc      = OllamaAdapter(model=PC_MODEL)        # control de PC
    brain_code    = OllamaAdapter(model=CODE_MODEL)      # summarizer del coding mode
"""
from __future__ import annotations

import os
import json
import base64
import logging
from typing import AsyncGenerator

from openai import AsyncOpenAI, APIConnectionError

logger = logging.getLogger(__name__)

# ── Variables de entorno ──────────────────────────────────────────────────────
OLLAMA_HOST   = os.getenv("OLLAMA_HOST",          "http://localhost:11434")
GENERAL_MODEL = os.getenv("JARVIS_GENERAL_MODEL", "gemma4:latest")
PC_MODEL      = os.getenv("JARVIS_PC_MODEL",      "qwen2.5-coder:latest")
CODE_MODEL    = os.getenv("JARVIS_CODE_MODEL",    "qwen2.5-coder:latest")

# ── System prompts ────────────────────────────────────────────────────────────

_SYSTEM_SUMMARIZER = """\
Eres J.A.R.V.I.S., asistente de voz para una persona con DISCAPACIDAD VISUAL TOTAL.
El usuario NO puede ver ninguna pantalla. Lo que respondas DEBE ser narrado oralmente.

── DETECTÁ EL TIPO DE PETICIÓN ─────────────────────────────────────────────
• EXPLICAR  → pide comprensión: "explícame", "qué es", "describí", "cómo funciona"
• EJECUTAR  → orden: "instalá", "creá", "borrá", "corré", "hacé", "commitear"
• ESTADO    → resultado: "cómo va", "qué pasó", "hay errores", "terminó"
• RESPUESTA → responde a Jarvis: "sí", "no", "dale", "uno", "dos", "tres"

── REGLAS POR TIPO ──────────────────────────────────────────────────────────
EXPLICAR → SIEMPRE hablar. Narrá los puntos clave de forma fluida y oral.
           No leas código ni rutas. Describí conceptos, propósitos y resultados.
           Usá 4-8 oraciones si el contenido lo justifica.

EJECUTAR → Hablar SOLO si: (a) completó exitosamente, (b) hay un error,
           (c) se requiere una decisión. Silencio en pasos intermedios.

ESTADO   → Hablar siempre. 2-3 oraciones: qué pasó, errores, próximo paso.

RESPUESTA → Hablar solo si el resultado fue relevante (éxito, error, decisión).

── SIEMPRE EN SILENCIO ──────────────────────────────────────────────────────
• Pensamientos internos (<thought>, <think>)
• Herramientas en background sin errores
• Planificación inicial sin resultado final

── PERSONALIDAD ─────────────────────────────────────────────────────────────
• Profesional y directo. Dirigite al usuario como "Señor".
• NUNCA leas: código fuente, rutas, asteriscos, markdown, símbolos técnicos.

── FORMATO JSON ESTRICTO (sin backticks) ────────────────────────────────────
{
  "intent_type": "EXPLICAR|EJECUTAR|ESTADO|RESPUESTA|DESCONOCIDO",
  "reasoning": "análisis interno breve",
  "should_speak": true|false,
  "speech_content": "texto exacto para TTS (vacío si should_speak es false)"
}
"""

_SYSTEM_CONVERSATIONAL = """\
Eres J.A.R.V.I.S. (Just A Rather Very Intelligent System), asistente de voz \
controlado 100% por voz.

REGLAS CRÍTICAS:
1. Respondés en el mismo idioma en que te hablan (español o inglés).
2. Tus respuestas son SIEMPRE cortas y directas — oraciones, no párrafos.
3. NUNCA leas código en voz alta. Si generás código, describí qué hace en una oración.
4. NUNCA leas rutas de archivo, URLs completas ni stack traces.
5. Si el usuario pide algo ambiguo, preguntá UNA sola cosa de aclaración.
6. Tratás al usuario como "Señor" cuando querés ser formal.
7. No usás emojis, markdown ni formato — hablás como humano.
"""

_SYSTEM_EVAL = """\
Eres la inteligencia central de JARVIS. Clasificás la intención del usuario. \
Respondés ÚNICAMENTE en JSON válido.\
"""


class OllamaAdapter:
    """
    Adaptador universal para Ollama.

    Uso básico:
        adapter = OllamaAdapter()                     # modelo general
        adapter = OllamaAdapter(model=PC_MODEL)       # modelo PC
        adapter = OllamaAdapter(model=CODE_MODEL)     # modelo coding

    Si Ollama no está corriendo, los métodos devuelven respuestas de fallback
    en lugar de crashear — Jarvis sigue funcionando degradado.
    """

    def __init__(self, model: str = GENERAL_MODEL) -> None:
        self.model = model
        self.client = AsyncOpenAI(
            base_url=f"{OLLAMA_HOST}/v1",
            api_key="ollama",  # Ollama no valida la key, pero el cliente la requiere
        )
        self._history: list[dict] = []
        logger.info(f"OllamaAdapter listo — modelo: {self.model} @ {OLLAMA_HOST}")

    # ── Summarizer (filtra output de terminal/TUI para TTS) ───────────────────

    async def summarize(self, raw_text: str, user_command: str = "") -> dict:
        """
        Evalúa la salida cruda de la terminal y decide si Jarvis debe hablar.
        Retorna el schema JSON del sistema actual.
        """
        prompt = (
            f"[ÚLTIMO COMANDO DEL USUARIO]:\n{user_command}\n\n"
            f"[SALIDA CRUDA A EVALUAR]:\n{raw_text}\n\n"
            f"[TU RESPUESTA EN JSON]:"
        )
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": _SYSTEM_SUMMARIZER},
                    {"role": "user",   "content": prompt},
                ],
                response_format={"type": "json_object"},
                temperature=0.2,
            )
            return json.loads(response.choices[0].message.content or "{}")
        except APIConnectionError:
            logger.error("Ollama no está corriendo — verificá que esté activo en localhost:11434")
            return self._fallback_summarize()
        except Exception as e:
            logger.error(f"OllamaAdapter.summarize error: {e}")
            return self._fallback_summarize()

    # ── Evaluador de respuesta del usuario ────────────────────────────────────

    async def evaluate_response(self, user_input: str, context: dict) -> dict:
        """
        Clasifica lo que dijo el usuario después de una intervención de Jarvis.
        Retorna: {"action": "authorize|answer|type|ignore", "value": str, "reasoning": str}
        """
        last_speech   = context.get("last_speech", "")
        last_terminal = context.get("last_terminal_output", "")

        prompt = f"""\
CONTEXTO:
- Lo que JARVIS dijo antes: "{last_speech}"
- Última salida de terminal: "{str(last_terminal)[:400]}"
- Lo que el usuario acaba de decir: "{user_input}"

CRITERIOS (en orden de prioridad):
1. "authorize" — El usuario APRUEBA. Señales: "sí", "dale", "ok", "uno", "dos", "tres".
   value: "1", "2" o "3" si hay opciones numeradas, sino "1".
2. "type" — Orden nueva y distinta. value: el comando exacto.
3. "answer" — Pregunta o pedido de aclaración. value: "".
   REGLA: si reformuló lo que dijo Jarvis → "answer", NUNCA "ignore".
4. "ignore" — SOLO ruido puro: onomatopeyas, silencio transcrito mal.

Respondé ÚNICAMENTE en JSON:
{{"action": "authorize|answer|type|ignore", "value": "string", "reasoning": "breve"}}
"""
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": _SYSTEM_EVAL},
                    {"role": "user",   "content": prompt},
                ],
                response_format={"type": "json_object"},
                temperature=0.2,
            )
            return json.loads(response.choices[0].message.content or "{}")
        except APIConnectionError:
            logger.error("Ollama no está corriendo.")
            return {"action": "answer", "value": "", "reasoning": "Ollama offline — fallback"}
        except Exception as e:
            logger.error(f"OllamaAdapter.evaluate_response error: {e}")
            return {"action": "answer", "value": "", "reasoning": f"Error: {e}"}

    # ── Summarizer de permisos ────────────────────────────────────────────────

    async def summarize_permission(self, details: dict) -> str:
        """
        Resume una solicitud de permiso de herramienta para leerla por voz.
        """
        prompt = f"""\
Analizá esta solicitud de permiso y generá un resumen natural para el usuario.
Detalles: {json.dumps(details, ensure_ascii=False)}

INSTRUCCIONES:
1. Identificá qué quiere hacer (borrar, editar, ejecutar, buscar, etc.).
2. Resumí el propósito en una frase corta.
3. Si hay una ruta o directorio, mencionala claramente.
4. Si la acción es peligrosa (borrar, modificar config crítica), advertilo.
5. Dirigite al usuario como "Señor".
6. Terminá SIEMPRE con: "Diga uno para permitir, dos para siempre o tres para denegar."

Respondé ÚNICAMENTE con el texto que Jarvis debe decir por voz. Sin JSON, sin etiquetas.
"""
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "Eres J.A.R.V.I.S. Resumís permisos de herramientas para el usuario."},
                    {"role": "user",   "content": prompt},
                ],
                temperature=0.3,
            )
            return (response.choices[0].message.content or "").strip()
        except APIConnectionError:
            return "Señor, el sistema requiere su autorización. Diga uno para permitir, dos para siempre o tres para denegar."
        except Exception as e:
            logger.error(f"OllamaAdapter.summarize_permission error: {e}")
            return "Señor, el sistema requiere su autorización. Diga uno para permitir, dos para siempre o tres para denegar."

    # ── Streaming conversacional (reemplaza ClaudeAPIAdapter.stream_response) ─

    async def stream_response(self, user_message: str) -> AsyncGenerator[tuple[str, str], None]:
        """
        Envía un mensaje y hace streaming de la respuesta.

        Yields:
            ("TEXT_CHUNK", str)  — fragmento de texto listo para TTS
            ("CODE_BLOCK", str)  — bloque de código para resumir antes de hablar
        """
        self._history.append({"role": "user", "content": user_message})
        collected: list[str] = []

        try:
            stream = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": _SYSTEM_CONVERSATIONAL},
                    *self._history,
                ],
                stream=True,
                temperature=0.7,
            )

            buffer = ""
            in_code_block = False

            async for chunk in stream:
                delta = chunk.choices[0].delta.content or ""
                if not delta:
                    continue

                collected.append(delta)
                buffer += delta

                # Detectar inicio/fin de bloque de código
                if "```" in buffer:
                    parts = buffer.split("```")
                    for i, part in enumerate(parts[:-1]):
                        if part.strip():
                            kind = "CODE_BLOCK" if in_code_block else "TEXT_CHUNK"
                            yield kind, part.strip()
                        in_code_block = not in_code_block
                    buffer = parts[-1]
                elif not in_code_block and any(buffer.endswith(p) for p in (".", "!", "?", "\n")):
                    if buffer.strip():
                        yield "TEXT_CHUNK", buffer.strip()
                    buffer = ""

            # Flush del buffer restante
            if buffer.strip():
                kind = "CODE_BLOCK" if in_code_block else "TEXT_CHUNK"
                yield kind, buffer.strip()

        except APIConnectionError:
            self._history.pop()
            yield "TEXT_CHUNK", "Señor, Ollama no está corriendo. Inicialo con 'ollama serve'."
            return
        except Exception as e:
            logger.error(f"OllamaAdapter.stream_response error: {e}")
            self._history.pop()
            yield "TEXT_CHUNK", "Señor, hubo un error al contactar el modelo local."
            return

        full = "".join(collected)
        if full:
            self._history.append({"role": "assistant", "content": full})
            self._compact_history()

    # ── Vision (Gemma 4 multimodal — describe screenshots) ───────────────────

    async def vision_describe(self, screenshot_bytes: bytes, prompt: str = "") -> str:
        """
        Envía un screenshot al modelo y pide una descripción oral.
        Requiere un modelo multimodal (gemma4, llava, etc.).

        Args:
            screenshot_bytes: PNG o JPEG en bytes.
            prompt: instrucción adicional. Si vacío, usa descripción general de accesibilidad.
        """
        if not prompt:
            prompt = (
                "Describí lo que ves en esta pantalla de forma oral y clara, "
                "como si se lo estuvieras explicando a una persona con discapacidad visual. "
                "Mencioná: aplicación activa, contenido principal, elementos interactivos visibles, "
                "y cualquier mensaje de error o alerta. Sé conciso — máximo 4 oraciones."
            )

        image_b64 = base64.b64encode(screenshot_bytes).decode("utf-8")

        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{image_b64}"}},
                        ],
                    }
                ],
                temperature=0.3,
            )
            return (response.choices[0].message.content or "").strip()
        except APIConnectionError:
            return "Señor, Ollama no está corriendo."
        except Exception as e:
            logger.error(f"OllamaAdapter.vision_describe error: {e}")
            return "Señor, no pude describir la pantalla."

    # ── Historial ─────────────────────────────────────────────────────────────

    def _compact_history(self) -> None:
        MAX = 40  # 20 turnos
        if len(self._history) > MAX:
            self._history = self._history[-MAX:]

    def abort_last_turn(self) -> None:
        if self._history and self._history[-1]["role"] == "user":
            self._history.pop()

    def reset_history(self) -> None:
        self._history = []

    @property
    def turn_count(self) -> int:
        return len(self._history) // 2

    # ── Fallbacks internos ────────────────────────────────────────────────────

    @staticmethod
    def _fallback_summarize() -> dict:
        return {
            "intent_type": "DESCONOCIDO",
            "reasoning": "Ollama offline o error de conexión",
            "should_speak": False,
            "speech_content": "",
        }
