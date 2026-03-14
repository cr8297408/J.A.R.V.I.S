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
from core.audio.vad_listener import start_vad_thread, awaiting_tool_permission
from adapters.llm.gemini_summarizer import GeminiSummarizer
from adapters.tts.mac_say_tts import MacSayTTS
from adapters.stt.ghost_typer import GhostTyper

# Evento global de Barge-in (Si se pone en True, el TTS se calla)
interrupt_event = threading.Event()

# Componentes globales del pipeline
lexer = StreamingLexer()
summarizer = GeminiSummarizer()
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
                        msg = payload.get(
                            "message", "Tool permission required."
                        )
                        prompt = f"{msg}. Say 1 to allow once, 2 to allow for this session, or 3 to deny."
                        logging.info(
                            "Notificación de herramienta detectada. Avisando al usuario."
                        )
                        tts.speak(prompt, interrupt_event)
                        awaiting_tool_permission.set()
                except Exception as e:
                    logging.error(f"Error parseando notificación: {e}")
                text_queue.task_done()
                continue

            # Si el usuario interrumpió hace poco (habló), limpiamos el estado del lexer
            # para no decir la mitad de una frase vieja o quedarnos atrapados en un bloque de código
            if interrupt_event.is_set():
                logging.info("Barge-in detectado: Reseteando Lexer y vaciando cola.")
                lexer.reset()  # Necesitamos agregar este método al Lexer
                interrupt_event.clear()

                # Vaciar la cola actual de texto viejo
                while not text_queue.empty():
                    try:
                        text_queue.get_nowait()
                        text_queue.task_done()
                    except asyncio.QueueEmpty:
                        break
                continue

            # Procesamos el token con el Lexer
            chunk_type, content = await lexer.process_token(chunk)

            if chunk_type == "TEXT_CHUNK" and content:
                logging.info(f"Hablando texto: {content}")
                # El TTS bloquea, pero eso está bien porque queremos que hable antes de seguir procesando.
                # Si necesitamos que no bloquee todo el demonio, podríamos correrlo en un executor,
                # pero para mantener el orden secuencial del habla, bloquear acá es correcto.
                tts.speak(content, interrupt_event)

            elif chunk_type == "CODE_BLOCK" and content:
                logging.info(
                    f"Resumiendo bloque de código de {len(content)} caracteres..."
                )
                try:
                    resumen = await summarizer.summarize(content)
                    logging.info(f"Resumen generado: {resumen}")
                    tts.speak(resumen, interrupt_event)
                except Exception as e:
                    logging.error(f"Error resumiendo código con Gemini Flash: {e}")

            text_queue.task_done()

        except Exception as e:
            logging.error(f"Error en el bucle de procesamiento: {e}")


async def handle_client(reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
    """
    Maneja las conexiones TCP entrantes del hook script.
    Lee el chunk, lo encola y responde con un ACK instantáneo.
    """
    addr = writer.get_extra_info("peername")
    try:
        data = await reader.read(
            8192
        )  # Leer hasta 8KB (suficiente para un chunk de LLM)
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
