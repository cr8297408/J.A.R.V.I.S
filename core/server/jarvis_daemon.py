import sys
import os
import asyncio
import threading
import logging

# Configurar logs básicos para el Daemon
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - [JARVIS DAEMON] - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("jarvis_daemon.log"),
    ],
)

# Asegurarnos de que Python encuentre nuestras carpetas locales (Project Root)
project_root = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)
sys.path.insert(0, project_root)

from core.lexer.poc_lexer import StreamingLexer
from core.audio.vad_listener import (
    start_vad_thread,
    active_listening_requested,
    jarvis_speaking,
    user_context,
)
from adapters.tts.edge_tts_adapter import EdgeTTS
from adapters.stt.ghost_typer import GhostTyper

# Importar dotenv para cargar variables de entorno
from dotenv import load_dotenv

load_dotenv()

# Evento global de Barge-in (Si se pone en True, el TTS se calla)
interrupt_event = threading.Event()

# Selección dinámica del cerebro (LLM) según el .env
active_brain = os.getenv("ACTIVE_BRAIN_ENGINE", "gemini").lower()

if active_brain == "groq":
    from adapters.llm.groq_summarizer import GroqSummarizer

    summarizer = GroqSummarizer()
    logging.info("🧠 Cerebro activado: Groq (Llama 3.3)")
elif active_brain == "openrouter":
    from adapters.llm.openrouter_summarizer import OpenRouterSummarizer

    summarizer = OpenRouterSummarizer()
    logging.info("🧠 Cerebro activado: OpenRouter")
else:
    from adapters.llm.gemini_summarizer import GeminiSummarizer

    summarizer = GeminiSummarizer()
    logging.info("🧠 Cerebro activado: Google AI Studio (Gemini)")

# Componentes globales del pipeline
lexer = StreamingLexer()
tts = EdgeTTS()

# Cola asíncrona para procesar los chunks que llegan por el socket en orden
text_queue = None


async def evaluar_y_hablar(texto_acumulado: str):
    """Envía un bloque de texto consolidado al Cerebro J.A.R.V.I.S."""
    if not texto_acumulado.strip():
        return

    logging.info(
        f"Procesando bloque de salida consolidado (len: {len(texto_acumulado)})"
    )
    try:
        logging.info("Consultando al cerebro J.A.R.V.I.S. si debe intervenir...")
        last_cmd = user_context.get("last_command", "")
        decision = await summarizer.summarize(texto_acumulado, last_cmd)

        reasoning = decision.get("reasoning", "Sin razonamiento")
        should_speak = decision.get("should_speak", False)
        speech = decision.get("speech_content", "")

        logging.info(f"[Cerebro JARVIS] Razonamiento: {reasoning}")

        if should_speak and speech:
            user_context["last_speech"] = speech
            user_context["last_terminal_output"] = texto_acumulado
            logging.info(f"[Cerebro JARVIS] Decidió hablar: {speech}")
            
            # Activamos la escucha PREVIO a hablar para permitir Barge-in siempre
            active_listening_requested.set()
            jarvis_speaking.set()

            # Hablar (bloqueante en el hilo de TTS)
            try:
                await asyncio.to_thread(tts.speak, speech, interrupt_event)
            finally:
                jarvis_speaking.clear()
        else:
            logging.info(
                "[Cerebro JARVIS] Decidió mantener silencio (Filtrando ruido cognitivo)."
            )
    except Exception as e:
        logging.error(f"Error procesando decisión de Jarvis: {e}")


async def process_text_queue():
    """
    Este es el 'Cerebro' asíncrono.
    Desencola los chunks que llegan por el socket, los acumula (debounce)
    para no evaluar fragmentos cortados, y luego los pasa al LLM.
    """
    logging.info("Motor de procesamiento de texto iniciado.")

    buffer = ""

    while True:
        try:
            if not buffer:
                # Si el buffer está vacío, esperar indefinidamente un chunk
                chunk = await text_queue.get()
            else:
                # Si tenemos texto acumulado, esperamos un poco más (debounce).
                # Si no llega nada en 1.5 segundos, asumimos que la terminal terminó de escupir datos.
                try:
                    chunk = await asyncio.wait_for(text_queue.get(), timeout=1.5)
                except asyncio.TimeoutError:
                    # Se acabó el tiempo, procesar lo que tenemos acumulado
                    await evaluar_y_hablar(buffer)
                    buffer = ""
                    continue

            # --- Procesamiento del chunk recibido ---

            if chunk.startswith("__NOTIFICATION__"):
                # Si nos llega una notificación y teníamos texto acumulado, lo evaluamos primero
                if buffer:
                    await evaluar_y_hablar(buffer)
                    buffer = ""

                payload_str = chunk[16:]
                import json

                try:
                    payload = json.loads(payload_str)
                    logging.info(f"Payload de notificación: {payload}")
                    if payload.get("notification_type") == "ToolPermission":
                        # Extraer mensaje de la notificación y detalles
                        message = payload.get("message", "")
                        details = payload.get("details", {})

                        tool_type = details.get("type", "")

                        if tool_type == "exec":
                            cmd = details.get("command", "un comando desconocido")
                            prompt = f"Señor, Gemini quiere ejecutar el comando: {cmd}. Diga uno para permitir, dos para siempre, o tres para denegar."
                        elif tool_type == "edit":
                            file_name = details.get("fileName", "un archivo")
                            prompt = f"Señor, Gemini quiere editar el archivo: {file_name}. Diga uno para permitir, dos para siempre, o tres para denegar."
                        elif tool_type == "mcp":
                            tool = details.get(
                                "toolDisplayName",
                                details.get("toolName", "una herramienta"),
                            )
                            server = details.get("serverName", "un servidor")
                            prompt = f"Señor, Gemini quiere usar la herramienta {tool} del servidor MCP {server}. Diga uno para permitir, dos para siempre, o tres para denegar."
                        else:
                            # Fallback si no sabemos el tipo
                            title = details.get("title", "una acción")
                            prompt = f"Señor, el protocolo requiere autorización para {title}. Diga uno para permitir, dos para siempre, o tres para denegar."

                        logging.info(
                            f"Notificación de herramienta detectada. Mensaje: {message} | Detalles: {details}. Avisando al usuario."
                        )

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

            # Si el usuario interrumpió hace poco (habló), limpiamos el estado
            if interrupt_event.is_set():
                logging.info("Barge-in detectado: Vaciando cola y buffer.")
                interrupt_event.clear()
                buffer = ""

                # Vaciar la cola actual de texto viejo
                while not text_queue.empty():
                    try:
                        text_queue.get_nowait()
                        text_queue.task_done()
                    except asyncio.QueueEmpty:
                        break
                continue

            # Acumular el texto normal de la terminal en lugar de procesarlo inmediatamente
            buffer += chunk + "\n"
            text_queue.task_done()

        except Exception as e:
            logging.error(f"Error en el bucle de procesamiento: {e}")


async def handle_client(reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
    """
    Maneja las conexiones TCP entrantes del hook script.
    Lee el chunk completo, lo encola y responde con un ACK instantáneo.
    """
    addr = writer.get_extra_info("peername")
    try:
        data = await reader.read()  # Leer hasta EOF
        if data:
            chunk = data.decode("utf-8").strip()
            if chunk:
                # Encolamos el texto para que el Cerebro lo procese
                await text_queue.put(chunk)

            # Mandamos un ACK (1 byte) para que el script cliente se cierre rápido y no se cuelgue
            writer.write(b"K")
            await writer.drain()
    except Exception as e:
        logging.error(f"Error manejando cliente {addr}: {e}")
    finally:
        writer.close()
        await writer.wait_closed()


async def start_server():
    """Inicia el servidor TCP local."""
    global text_queue
    if text_queue is None:
        text_queue = asyncio.Queue()

    server = await asyncio.start_server(handle_client, "127.0.0.1", 49999)

    addrs = ", ".join(str(sock.getsockname()) for sock in server.sockets)
    logging.info(f"Jarvis Daemon escuchando en {addrs}")

    async with server:
        # Arrancamos la tarea que procesa la cola de texto
        asyncio.create_task(process_text_queue())
        await server.serve_forever()


def main():
    print("\r\n[J.A.R.V.I.S] Inicializando el Demonio Maestro...\r\n")

    # 1. Abrimos una terminal dedicada con gemini-cli
    logging.info("Aislando entorno: Lanzando Terminal nueva con Gemini...")
    GhostTyper.launch_gemini_terminal()

    # 2. Inicializamos el bucle de eventos principal (asyncio)
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    # 3. Arrancamos el Micrófono (VAD) en un hilo demonio para el Barge-in
    logging.info("Iniciando motor VAD (Voice Activity Detection)...")
    start_vad_thread(interrupt_event, summarizer, tts, loop)

    # 4. Arrancamos el servidor TCP Asíncrono en el hilo principal
    try:
        loop.run_until_complete(start_server())
    except KeyboardInterrupt:
        logging.info("Apagando Jarvis Daemon...")
    except Exception as e:
        logging.critical(f"Error fatal en el Demonio: {e}")
    finally:
        loop.close()


if __name__ == "__main__":
    main()
