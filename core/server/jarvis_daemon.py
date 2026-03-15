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
    awaiting_tool_permission,
    user_context,
)
from adapters.tts.mac_say_tts import MacSayTTS
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
tts = MacSayTTS()

# Cola asíncrona para procesar los chunks que llegan por el socket en orden
text_queue = asyncio.Queue()


async def process_text_queue():
    """
    Este es el 'Cerebro' asíncrono.
    Desencola los chunks que llegan por el socket, los pasa por el Lexer,
    resume el código si es necesario y dispara el TTS.
    """
    logging.info("Motor de procesamiento de texto iniciado.")

    while True:
        try:
            chunk = await text_queue.get()

            if chunk.startswith("__NOTIFICATION__"):
                payload_str = chunk[16:]
                import json

                try:
                    payload = json.loads(payload_str)
                    if payload.get("notification_type") == "ToolPermission":
                        # Adaptamos el prompt del sistema al estilo Jarvis para notificaciones
                        tool_name = payload.get(
                            "tool_name", "una herramienta desconocida"
                        )
                        prompt = f"Señor, el protocolo requiere autorización para ejecutar un comando. Diga uno para permitir una vez, dos para la sesión, o tres para denegar."
                        logging.info(
                            "Notificación de herramienta detectada. Avisando al usuario."
                        )
                        await asyncio.to_thread(tts.speak, prompt, interrupt_event)
                        awaiting_tool_permission.set()
                except Exception as e:
                    logging.error(f"Error parseando notificación: {e}")
                text_queue.task_done()
                continue

            # Si el usuario interrumpió hace poco (habló), limpiamos el estado
            if interrupt_event.is_set():
                logging.info("Barge-in detectado: Vaciando cola.")
                interrupt_event.clear()

                # Vaciar la cola actual de texto viejo
                while not text_queue.empty():
                    try:
                        text_queue.get_nowait()
                        text_queue.task_done()
                    except asyncio.QueueEmpty:
                        break
                continue

            # Log para debuggear el payload
            logging.info(f"Procesando bloque de salida (len: {len(chunk)})")

            # En vez de usar el Lexer para texto plano, enviamos todo al Cerebro J.A.R.V.I.S.
            # para que decida de forma autónoma si debe hablar o guardar silencio.
            try:
                logging.info(
                    "Consultando al cerebro J.A.R.V.I.S. si debe intervenir..."
                )
                last_cmd = user_context.get("last_command", "")
                decision = await summarizer.summarize(chunk, last_cmd)

                reasoning = decision.get("reasoning", "Sin razonamiento")
                should_speak = decision.get("should_speak", False)
                speech = decision.get("speech_content", "")

                logging.info(f"[Cerebro JARVIS] Razonamiento: {reasoning}")

                if should_speak and speech:
                    logging.info(f"[Cerebro JARVIS] Decidió hablar: {speech}")
                    await asyncio.to_thread(tts.speak, speech, interrupt_event)
                else:
                    logging.info(
                        "[Cerebro JARVIS] Decidió mantener silencio (Filtrando ruido cognitivo)."
                    )

            except Exception as e:
                logging.error(f"Error procesando decisión de Jarvis: {e}")

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

    # 2. Arrancamos el Micrófono (VAD) en un hilo demonio para el Barge-in
    logging.info("Iniciando motor VAD (Voice Activity Detection)...")
    start_vad_thread(interrupt_event)

    # 3. Arrancamos el servidor TCP Asíncrono en el hilo principal
    try:
        asyncio.run(start_server())
    except KeyboardInterrupt:
        logging.info("Apagando Jarvis Daemon...")
    except Exception as e:
        logging.critical(f"Error fatal en el Demonio: {e}")


if __name__ == "__main__":
    main()
