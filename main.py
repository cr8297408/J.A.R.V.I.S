import sys
import os
import time
import select
import tty
import termios
import threading
import asyncio
import re

# Asegurarnos de que Python encuentre nuestras carpetas locales
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.cli.pty_wrapper import PtyCLIWrapper
from core.lexer.poc_lexer import StreamingLexer
from core.audio.vad_listener import start_vad_thread
from adapters.llm.gemini_summarizer import GeminiSummarizer
from adapters.tts.mac_say_tts import MacSayTTS

# Evento global de Barge-in (Si se pone en True, el TTS se calla)
interrupt_event = threading.Event()

# Regex para limpiar los colores de la terminal (Códigos ANSI)
ANSI_CLEANER = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")
BOX_DRAWING_CLEANER = re.compile(
    r"[─━│┃┄┅┆┇┈┉┊┋┌┍┎┏┐┑┒┓└┕┖┗┘┙┚┛├┝┞┟┠┡┢┣┤┥┦┧┨┩┪┫┬┭┮┯┰┱┲┳┴┵┶┷┸┹┺┻┼┽┾┿╀╁╂╃╄╅╆╇╈╉╊╋═║╒╓╔╕╖╗╘╙╚╛╜╝╞╟╠╡╢╣╤╥╦╧╨╩╪╫╬╭╮╯╰╱╲╳╴╵╶╷╸╹╺╻╼╽╾╿▀▂▃▄▅▆▇█▉▊▋▌▍▎▏▐░▒▓▔▕▖▗▘▙▚▛▜▝▞▟]+"
)
TITLE_CLEANER = re.compile(
    r"\x1b\]0;.*?\x07"
)  # Limpia el título de la ventana que tira iTerm2


async def brain_async_loop(text_queue: asyncio.Queue, loop: asyncio.AbstractEventLoop):
    """
    Este es 'El Cerebro' asíncrono.
    Corre en un hilo separado. Lee el texto limpio que le manda el Orquestador,
    lo parsea (Lexer), lo resume (LLM si es código) y lo habla (TTS).
    """
    lexer = StreamingLexer()
    summarizer = GeminiSummarizer()
    tts = MacSayTTS()

    while True:
        # Esperamos el próximo chunk de texto limpio
        chunk = await text_queue.get()

        # Si el usuario interrumpió hace un segundo, limpiamos el estado del lexer para no hablar cosas viejas
        if interrupt_event.is_set():
            lexer.buffer = ""
            lexer.in_code_block = False
            interrupt_event.clear()  # Bajamos la bandera porque ya nos callamos

        chunk_type, content = await lexer.process_token(chunk)

        if chunk_type == "TEXT_CHUNK":
            # Lo mandamos a hablar directo (bloquea este hilo asíncrono hasta que termina de hablar o lo interrumpen)
            tts.speak(content, interrupt_event)

        elif chunk_type == "CODE_BLOCK":
            try:
                # Resumimos usando Gemini Flash y luego hablamos
                resumen = await summarizer.summarize(content)
                tts.speak(resumen, interrupt_event)
            except Exception as e:
                # Si falla la API de Gemini, no queremos que crashee todo el programa
                pass


def start_brain_thread(text_queue: asyncio.Queue, loop: asyncio.AbstractEventLoop):
    """Inicializa el bucle asíncrono en un hilo demonio."""
    asyncio.set_event_loop(loop)
    loop.run_until_complete(brain_async_loop(text_queue, loop))


# Lista de basura de la UI: Si una línea contiene ALGO de esto, se descarta la línea ENTERA.
TUI_BLACKLIST = [
    "shift+tab",
    "Press 'Esc'",
    "[INSERT]",
    "Gemini CLI",
    "Logged in with Google",
    "Gemini Code Assist",
    "GEMINI.md",
    "sandbox",
    "/model Auto",
    "see /docs",
    "(Gemini 3)",
    "? for shortcuts",
    "Ready (",
]


def clean_and_filter_chunk(raw_chunk: str) -> str:
    """
    Toma un chunk crudo de la TUI, lo separa por líneas y aplica la guillotina.
    Si una línea tiene basura de la UI, vuela completa.
    """
    # Unificamos saltos de línea raros
    normalized_chunk = raw_chunk.replace("\r\n", "\n").replace("\r", "\n")
    lines = normalized_chunk.split("\n")

    valid_lines = []

    for line in lines:
        # 1. Sacamos los colores para poder leer el texto
        clean_line = ANSI_CLEANER.sub("", line)

        # 2. Si la línea menciona el directorio actual, vuela
        current_dir = os.path.basename(os.getcwd())
        if current_dir in clean_line:
            continue

        # 3. Si la línea tiene alguna palabra prohibida de la UI, VUELA COMPLETA
        if any(bad_word in clean_line for bad_word in TUI_BLACKLIST):
            continue

        # 4. Sacamos los caracteres de dibujo (cajas, líneas de markdown) y títulos
        clean_line = BOX_DRAWING_CLEANER.sub("", clean_line)
        clean_line = TITLE_CLEANER.sub("", clean_line)

        # 5. Limpiamos caracteres sueltos que usa Gemini como viñetas o prompts
        clean_line = clean_line.replace("✦", "").replace("◇", "").strip()

        # 6. Si después de toda la limpieza la línea quedó vacía o es solo un ">", la descartamos
        if len(clean_line) < 2 and clean_line in ("", ">"):
            continue

        valid_lines.append(clean_line)

    return " ".join(valid_lines).strip()


def main():
    # Borramos el log viejo si existe para arrancar limpios
    if os.path.exists("debug_jarvis.log"):
        os.remove("debug_jarvis.log")

    print("\r\n[J.A.R.V.I.S] Inicializando el Sistema Maestro...\r\n")

    # 1. Arrancamos el Micrófono (VAD) para el Barge-in
    start_vad_thread(interrupt_event)

    # 2. Arrancamos el Cerebro en su propio hilo (Para que no congele la terminal)
    brain_loop = asyncio.new_event_loop()
    text_queue = asyncio.Queue()
    threading.Thread(
        target=start_brain_thread, args=(text_queue, brain_loop), daemon=True
    ).start()

    # 3. Preparamos el PTY Wrapper
    wrapper = PtyCLIWrapper(["gemini"])

    # Salvamos el teclado
    try:
        old_tty = termios.tcgetattr(sys.stdin.fileno())
    except Exception:
        old_tty = None

    try:
        wrapper.start()
        tty.setraw(sys.stdin.fileno())

        # Estado para saber si el usuario está tipeando y así NO leer su eco local
        is_user_typing = True

        # BUCLE PRINCIPAL (Multiplexación I/O)
        while wrapper.running and wrapper.fd is not None:
            rlist, _, _ = select.select([sys.stdin, wrapper.fd], [], [], 0.05)

            # Caso 1: Escribimos en el teclado
            if sys.stdin in rlist:
                char = os.read(sys.stdin.fileno(), 1)
                if not char:
                    break

                if char == b"\x03":  # Ctrl+C
                    raise KeyboardInterrupt

                # Si aprieta Enter (Submit), asumimos que dejó de tipear y Gemini va a empezar a responder
                if char in (b"\r", b"\n"):
                    is_user_typing = False
                    # Limpiamos cualquier basura vieja que haya quedado en la cola
                    interrupt_event.set()
                else:
                    # Si tipea cualquier otra cosa (letras, flechas, borrar), silenciamos a J.A.R.V.I.S
                    is_user_typing = True
                    interrupt_event.set()

                os.write(wrapper.fd, char)

            # Caso 2: Gemini escupe datos por la terminal
            if wrapper.fd in rlist:
                chunk = wrapper.read_stream_non_blocking()
                if chunk:
                    # A. Imprimimos el chunk EXACTO con colores para el ojo humano SIEMPRE
                    sys.stdout.write(chunk)
                    sys.stdout.flush()

                    # DEBUG: Guardamos lo crudo y lo limpio para entender cómo dibuja la CLI
                    with open("debug_jarvis.log", "a", encoding="utf-8") as f:
                        f.write(f"\n--- RAW CHUNK ---\n{repr(chunk)}\n")

                    # Si el usuario está tipeando, NO LE MANDAMOS NADA AL CEREBRO
                    if is_user_typing:
                        continue

                    # B. Pasamos el chunk por la guillotina de TUI
                    clean_chunk = clean_and_filter_chunk(chunk)

                    with open("debug_jarvis.log", "a", encoding="utf-8") as f:
                        f.write(f"--- CLEAN CHUNK ---\n{repr(clean_chunk)}\n")

                    # C. Le pasamos el texto limpio a la cola
                    if clean_chunk:
                        brain_loop.call_soon_threadsafe(
                            text_queue.put_nowait, clean_chunk
                        )

    except KeyboardInterrupt:
        pass
    finally:
        if old_tty:
            termios.tcsetattr(sys.stdin.fileno(), termios.TCSADRAIN, old_tty)
        wrapper.stop()


if __name__ == "__main__":
    main()
