"""
Jarvis Daemon — servidor principal con tres modos de operación.

Modos:
    GENERAL  → conversación libre con gemma4:general via Ollama
    PC       → control de cualquier app via Accessibility API + gemma4:pc
    CODING   → agente de programación con OpenCode + Ollama (sesión PTY aparte)

Flujo de voz:
    Micrófono → VAD → Whisper → IntentRouter → modo correcto
                                    ↓ GENERAL     ↓ PC
                              OllamaAdapter   ToolDispatcher
                              stream_response  (Accessibility API)
                                    ↓               ↓
                                   TTS ←───────────┘

El modo CODING se activa lanzando OpenCodePtySession por separado (main.py o jarvis/cli.py).
Este daemon maneja GENERAL y PC, más las notificaciones de permisos de herramientas.
"""
import sys
import os
import asyncio
import threading
import logging
import time
import json

# ── Logging ───────────────────────────────────────────────────────────────────

def _log_path() -> str:
    if sys.platform == "darwin":
        log_dir = os.path.expanduser("~/Library/Logs/JARVIS")
    elif sys.platform == "win32":
        log_dir = os.path.join(os.getenv("APPDATA", os.path.expanduser("~")), "JARVIS", "logs")
    else:
        log_dir = os.path.expanduser("~/.local/share/jarvis/logs")
    os.makedirs(log_dir, exist_ok=True)
    return os.path.join(log_dir, "jarvis_daemon.log")


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - [JARVIS DAEMON] - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(_log_path()),
    ],
)

# ── Path setup ────────────────────────────────────────────────────────────────

project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

from dotenv import load_dotenv
load_dotenv()

# ── Imports del pipeline ──────────────────────────────────────────────────────

from core.audio.vad_listener import (
    start_vad_thread,
    active_listening_requested,
    jarvis_speaking,
    user_context,
)
from adapters.tts.edge_tts_adapter import EdgeTTS
from adapters.llm.ollama_adapter import OllamaAdapter, GENERAL_MODEL, PC_MODEL
from core.intent_router import IntentRouter, ModeState, Mode
from core.screen_reader.engine import create_screen_reader
from core.tool_dispatch.dispatcher import ToolDispatcher
from core.tool_dispatch.registry import TOOLS

# ── Estado global ─────────────────────────────────────────────────────────────

interrupt_event = threading.Event()
text_queue: asyncio.Queue | None = None

# Cerebros
brain_general = OllamaAdapter(model=GENERAL_MODEL)
brain_pc      = OllamaAdapter(model=PC_MODEL)

# Router de modos
mode_state = ModeState()
router     = IntentRouter(state=mode_state)

# Screen reader y dispatcher (se inicializan con el brain_pc para Vision fallback)
screen_reader = create_screen_reader(vision_adapter=brain_pc)
dispatcher    = ToolDispatcher(
    screen_reader=screen_reader,
    confirmation_callback=None,  # Se setea en main() cuando el loop async está listo
)

# TTS
tts = EdgeTTS()

logging.info(f"Cerebros Ollama listos — general: {GENERAL_MODEL} | pc: {PC_MODEL}")


# ── Pipeline de voz (on_transcription callback) ───────────────────────────────

def make_transcription_callback(loop: asyncio.AbstractEventLoop):
    """
    Genera el callback que recibe texto de Whisper y lo enruta al modo correcto.

    Este callback corre en el hilo del VAD listener.
    Usa run_coroutine_threadsafe para disparar corutinas en el loop async del daemon.
    """

    async def _handle_general(text: str):
        """Modo GENERAL: stream_response → TTS."""
        active_listening_requested.set()
        jarvis_speaking.set()
        try:
            async for chunk_type, content in brain_general.stream_response(text):
                if interrupt_event.is_set():
                    brain_general.abort_last_turn()
                    break
                if content:
                    await asyncio.to_thread(tts.speak, content, interrupt_event)
        finally:
            jarvis_speaking.clear()

    async def _handle_pc(text: str):
        """
        Modo PC: enviar texto a gemma4:pc con function calling → ToolDispatcher.
        gemma4:pc decide qué herramienta usar; el dispatcher la ejecuta.
        """
        try:
            response = await brain_pc.client.chat.completions.create(
                model=brain_pc.model,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "Eres J.A.R.V.I.S., asistente de control de PC por voz para usuario con discapacidad visual. "
                            "Analizás el comando del usuario y usás las herramientas disponibles para ejecutar la acción solicitada. "
                            "Si el comando no requiere una herramienta (es solo una pregunta), respondé directamente. "
                            "Siempre respondé de forma concisa y oral. Dirigite al usuario como 'Señor'."
                        ),
                    },
                    {"role": "user", "content": text},
                ],
                tools=TOOLS,
                tool_choice="auto",
                temperature=0.1,
            )

            message = response.choices[0].message

            # Si Gemma quiere usar una herramienta
            if message.tool_calls:
                for tool_call in message.tool_calls:
                    func = tool_call.function
                    result = await dispatcher.execute_tool_call({
                        "name": func.name,
                        "arguments": func.arguments,
                    })
                    if result:
                        jarvis_speaking.set()
                        try:
                            await asyncio.to_thread(tts.speak, result, interrupt_event)
                        finally:
                            jarvis_speaking.clear()
            # Si Gemma responde directo (sin herramienta)
            elif message.content:
                jarvis_speaking.set()
                try:
                    await asyncio.to_thread(tts.speak, message.content, interrupt_event)
                finally:
                    jarvis_speaking.clear()

        except Exception as e:
            logging.error(f"Error en modo PC: {e}")
            await asyncio.to_thread(
                tts.speak,
                "Señor, hubo un error al procesar el comando de control de PC.",
                interrupt_event,
            )

    def on_transcription(text: str):
        """
        Callback llamado por el VAD listener con el texto transcripto.
        Enruta al modo correcto según IntentRouter.
        """
        if not text.strip():
            return

        mode = router.route(text)
        user_context["last_command"] = text
        logging.info(f"[IntentRouter] '{text[:60]}' → {mode.value}")

        if mode == Mode.PC:
            asyncio.run_coroutine_threadsafe(_handle_pc(text), loop)
        elif mode == Mode.CODING:
            # El modo coding corre en su propia sesión PTY (OpenCodePtySession).
            # Desde aquí solo avisamos al usuario cómo activarlo.
            msg = "Señor, para el modo coding ejecute jarvis en modo código desde la terminal."
            asyncio.run_coroutine_threadsafe(
                asyncio.to_thread(tts.speak, msg, interrupt_event), loop
            )
        else:
            asyncio.run_coroutine_threadsafe(_handle_general(text), loop)

    return on_transcription


# ── Pipeline de notificaciones (TCP server) ───────────────────────────────────

async def evaluar_y_hablar(texto_acumulado: str):
    """Evalúa output de terminal y decide si Jarvis debe hablar."""
    if not texto_acumulado.strip():
        return

    logging.info(f"Procesando bloque de salida (len: {len(texto_acumulado)})")
    try:
        last_cmd = user_context.get("last_command", "")
        decision = await brain_general.summarize(texto_acumulado, last_cmd)

        should_speak = decision.get("should_speak", False)
        speech       = decision.get("speech_content", "")

        logging.info(f"[Cerebro] {decision.get('reasoning', '')}")

        if should_speak and speech:
            user_context["last_speech"] = speech
            user_context["last_terminal_output"] = texto_acumulado
            active_listening_requested.set()
            jarvis_speaking.set()
            try:
                await asyncio.to_thread(tts.speak, speech, interrupt_event)
            finally:
                jarvis_speaking.clear()
    except Exception as e:
        logging.error(f"Error en evaluar_y_hablar: {e}")


async def process_text_queue():
    """
    Cerebro async: debounce de chunks de terminal → LLM → TTS.
    Igual que antes pero usando OllamaAdapter en lugar de Gemini/Groq/OpenRouter.
    """
    logging.info("Motor de procesamiento de texto iniciado.")
    buffer = ""

    while True:
        try:
            if not buffer:
                chunk = await text_queue.get()
            else:
                try:
                    chunk = await asyncio.wait_for(text_queue.get(), timeout=1.5)
                except asyncio.TimeoutError:
                    await evaluar_y_hablar(buffer)
                    buffer = ""
                    continue

            # Notificaciones de permisos de herramientas (OpenCode / cualquier CLI)
            if chunk.startswith("__NOTIFICATION__"):
                if buffer:
                    await evaluar_y_hablar(buffer)
                    buffer = ""

                payload_str = chunk[16:]
                try:
                    payload = json.loads(payload_str)
                    if payload.get("notification_type") == "ToolPermission":
                        details = payload.get("details", {})
                        details["cwd_context"] = os.getenv("JARVIS_INVOCATION_DIR", os.getcwd())
                        user_context["pending_permission_ts"] = time.monotonic()

                        prompt = await brain_general.summarize_permission(details)
                        if interrupt_event.is_set():
                            interrupt_event.clear()

                        active_listening_requested.set()
                        jarvis_speaking.set()
                        try:
                            await asyncio.to_thread(tts.speak, prompt, interrupt_event)
                        finally:
                            jarvis_speaking.clear()
                except Exception as e:
                    logging.error(f"Error parseando notificación: {e}")

                text_queue.task_done()
                continue

            # Barge-in: limpiar estado
            if interrupt_event.is_set():
                interrupt_event.clear()
                buffer = ""
                while not text_queue.empty():
                    try:
                        text_queue.get_nowait()
                        text_queue.task_done()
                    except asyncio.QueueEmpty:
                        break
                continue

            buffer += chunk + "\n"
            text_queue.task_done()

        except Exception as e:
            logging.error(f"Error en el bucle de procesamiento: {e}")


async def handle_client(reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
    """Maneja conexiones TCP del hook script (notificaciones de herramientas)."""
    try:
        data = await reader.read()
        if data:
            chunk = data.decode("utf-8").strip()
            if chunk:
                await text_queue.put(chunk)
            writer.write(b"K")
            await writer.drain()
    except Exception as e:
        logging.error(f"Error manejando cliente TCP: {e}")
    finally:
        writer.close()
        await writer.wait_closed()


async def start_server():
    global text_queue
    if text_queue is None:
        text_queue = asyncio.Queue()

    server = await asyncio.start_server(handle_client, "127.0.0.1", 49999)
    addrs = ", ".join(str(sock.getsockname()) for sock in server.sockets)
    logging.info(f"Jarvis Daemon escuchando en {addrs}")

    async with server:
        asyncio.create_task(process_text_queue())
        await server.serve_forever()


# ── Confirmación vocal para ToolDispatcher ────────────────────────────────────

def make_confirmation_callback(loop: asyncio.AbstractEventLoop):
    """
    Genera el callback de confirmación vocal para ToolDispatcher.
    El dispatcher llama a esto antes de ejecutar acciones peligrosas.
    """
    async def _ask(message: str) -> bool:
        """Habla el mensaje y espera respuesta de voz del usuario."""
        # Hablar la pregunta
        jarvis_speaking.set()
        active_listening_requested.set()
        try:
            await asyncio.to_thread(tts.speak, message, interrupt_event)
        finally:
            jarvis_speaking.clear()

        # Esperar transcripción (el VAD listener actualiza user_context["last_command"])
        await asyncio.sleep(4.0)
        response = user_context.get("last_command", "").lower()
        return any(w in response for w in ("sí", "si", "dale", "ok", "adelante", "procede"))

    def sync_confirm(message: str) -> bool:
        future = asyncio.run_coroutine_threadsafe(_ask(message), loop)
        try:
            return future.result(timeout=15.0)
        except Exception:
            return False

    return sync_confirm


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    print("\r\n[J.A.R.V.I.S] Inicializando Daemon — Gemma 4 Local + Ollama...\r\n")
    logging.info(f"Modos disponibles: GENERAL ({GENERAL_MODEL}), PC ({PC_MODEL})")
    logging.info("Asegurate de que Ollama esté corriendo: ollama serve")

    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    # Inyectar callback de confirmación ahora que tenemos el loop
    dispatcher._confirm = make_confirmation_callback(loop)

    # Callback de transcripción con IntentRouter
    on_transcription = make_transcription_callback(loop)

    # VAD listener con callback directo (sin GhostTyper — el router decide qué hacer)
    logging.info("Iniciando motor VAD (Voice Activity Detection)...")
    start_vad_thread(
        interrupt_event,
        summarizer=brain_general,   # Para evaluate_response en modo legacy
        tts=tts,
        loop=loop,
        on_transcription=on_transcription,
    )

    # Servidor TCP para notificaciones de herramientas
    try:
        loop.run_until_complete(start_server())
    except KeyboardInterrupt:
        logging.info("Apagando Jarvis Daemon...")
    except Exception as e:
        logging.critical(f"Error fatal en el Daemon: {e}")
    finally:
        loop.close()


if __name__ == "__main__":
    main()
