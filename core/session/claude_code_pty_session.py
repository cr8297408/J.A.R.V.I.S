"""
ClaudeCodePtySession — PTY wrapper para Claude Code CLI.

Mismo patrón que main.py (Gemini), pero con filtros TUI específicos
para el React/Ink renderer de Claude Code.

Flujo:
    User speaks → VAD → Whisper → GhostTyper → PTY(claude) → TUI filter → TTS
"""
from __future__ import annotations

import os
import sys
import select
import tty
import termios
import threading
import asyncio
import re
import logging

logger = logging.getLogger(__name__)

# ── Regex para limpiar ruido de la terminal ───────────────────────────────────

ANSI_CLEANER = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")
BOX_DRAWING_CLEANER = re.compile(
    r"[─━│┃┄┅┆┇┈┉┊┋┌┍┎┏┐┑┒┓└┕┖┗┘┙┚┛├┝┞┟┠┡┢┣┤┥┦┧┨┩┪┫┬┭┮┯┰┱┲┳┴┵┶┷┸┹┺┻┼┽┾┿╀╁╂╃╄╅╆╇╈╉╊╋═║╒╓╔╕╖╗╘╙╚╛╜╝╞╟╠╡╢╣╤╥╦╧╨╩╪╫╬╭╮╯╰╱╲╳╴╵╶╷╸╹╺╻╼╽╾╿▀▂▃▄▅▆▇█▉▊▋▌▍▎▏▐░▒▓▔▕▖▗▘▙▚▛▜▝▞▟]+"
)
TITLE_CLEANER = re.compile(r"\x1b\]0;.*?\x07")

# Spinner Braille que usa Ink/React para loading indicators
SPINNER_CLEANER = re.compile(r"[⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏]+")

# ── Filtros específicos de Claude Code TUI ────────────────────────────────────

# Si una línea contiene CUALQUIERA de estas cadenas, se descarta COMPLETA.
# Son artefactos del React/Ink renderer de Claude Code.
TUI_BLACKLIST = [
    # Hints de teclado (status bar inferior)
    "Press Esc",
    "for newline",
    "! for bash",
    "? for help",
    "shift+tab",
    "auto-accept edits",
    "⏎",
    # Información del modelo en el header
    "Claude Code",
    "claude.ai/code",
    # Contadores de costo y tokens
    "Cost: $",
    "tokens",
    "input tokens",
    "output tokens",
    # Decoradores de tool calls que no son contenido útil
    "Running tool",
    "Tool result",
    "bash(",
    "read_file(",
    "write_file(",
    "list_files(",
    "search_files(",
    # Prompt vacío
    "◯",
    "●",
]


def clean_and_filter_chunk(raw_chunk: str) -> str:
    """
    Filtra el chunk de salida de Claude Code CLI:
    - Elimina códigos ANSI, box drawing, títulos de ventana
    - Elimina spinners Braille
    - Descarta líneas que son puro chrome del TUI
    - Preserva el contenido real de la respuesta
    """
    normalized = raw_chunk.replace("\r\n", "\n").replace("\r", "\n")
    lines = normalized.split("\n")
    valid_lines = []

    for line in lines:
        # 1. Eliminar escape sequences de color/posición
        clean = ANSI_CLEANER.sub("", line)

        # 2. Filtrar por contenido de directorio actual
        current_dir = os.path.basename(os.getcwd())
        if current_dir in clean:
            continue

        # 3. Guillotina: si la línea tiene chrome del TUI, vuela completa
        if any(bad in clean for bad in TUI_BLACKLIST):
            continue

        # 4. Eliminar box drawing, títulos, spinners
        clean = BOX_DRAWING_CLEANER.sub("", clean)
        clean = TITLE_CLEANER.sub("", clean)
        clean = SPINNER_CLEANER.sub("", clean)

        # 5. Limpiar símbolos decorativos de Claude Code
        clean = clean.replace("✓", "").replace("✗", "").replace("►", "")
        clean = clean.replace("▶", "").replace("·", "").strip()

        # 6. Descartar líneas vacías o que son solo el prompt ">"
        if len(clean) < 2 and clean in ("", ">", "$"):
            continue

        valid_lines.append(clean)

    return " ".join(valid_lines).strip()


# ── Sesión PTY ────────────────────────────────────────────────────────────────

class ClaudeCodePtySession:
    """
    Wrapper PTY para Claude Code CLI con overlay de voz.

    Uso:
        session = ClaudeCodePtySession()
        session.run()  # bloqueante hasta Ctrl+C
    """

    def __init__(self) -> None:
        from adapters.tts.mac_say_tts import MacSayTTS
        from core.lexer.poc_lexer import StreamingLexer

        self.tts = MacSayTTS()
        self.interrupt_event = threading.Event()
        self._lexer_class = StreamingLexer

    def run(self) -> None:
        """Inicia la sesión PTY. Bloqueante hasta Ctrl+C."""
        from core.cli.pty_wrapper import PtyCLIWrapper
        from core.audio.vad_listener import start_vad_thread

        print("\r\n[J.A.R.V.I.S] Modo PTY — Claude Code. Inicializando...\r\n")

        # Arrancar cerebro async en su hilo
        brain_loop = asyncio.new_event_loop()
        text_queue: asyncio.Queue = asyncio.Queue()
        threading.Thread(
            target=self._brain_thread,
            args=(text_queue, brain_loop),
            daemon=True,
        ).start()

        # Arrancar VAD (usa GhostTyper para inyectar voz en el PTY)
        start_vad_thread(self.interrupt_event)

        # Iniciar el wrapper PTY
        wrapper = PtyCLIWrapper(["claude"])

        try:
            old_tty = termios.tcgetattr(sys.stdin.fileno())
        except Exception:
            old_tty = None

        try:
            wrapper.start()
            tty.setraw(sys.stdin.fileno())

            is_user_typing = True

            while wrapper.running and wrapper.fd is not None:
                rlist, _, _ = select.select([sys.stdin, wrapper.fd], [], [], 0.05)

                # Teclado → PTY
                if sys.stdin in rlist:
                    char = os.read(sys.stdin.fileno(), 1)
                    if not char:
                        break

                    if char == b"\x03":  # Ctrl+C
                        raise KeyboardInterrupt

                    if char in (b"\r", b"\n"):
                        is_user_typing = False
                        self.interrupt_event.set()
                    else:
                        is_user_typing = True
                        self.interrupt_event.set()

                    os.write(wrapper.fd, char)

                # PTY → pantalla + TTS
                if wrapper.fd in rlist:
                    chunk = wrapper.read_stream_non_blocking()
                    if chunk:
                        sys.stdout.write(chunk)
                        sys.stdout.flush()

                        if is_user_typing:
                            continue

                        clean_chunk = clean_and_filter_chunk(chunk)
                        if clean_chunk:
                            brain_loop.call_soon_threadsafe(
                                text_queue.put_nowait, clean_chunk
                            )

        except KeyboardInterrupt:
            logger.info("Sesión PTY Claude Code terminada por el usuario.")
        finally:
            if old_tty:
                termios.tcsetattr(sys.stdin.fileno(), termios.TCSADRAIN, old_tty)
            wrapper.stop()

    def _brain_thread(self, text_queue: asyncio.Queue, loop: asyncio.AbstractEventLoop) -> None:
        """Hilo del cerebro: Lexer → TTS."""
        asyncio.set_event_loop(loop)
        loop.run_until_complete(self._brain_async_loop(text_queue))

    async def _brain_async_loop(self, text_queue: asyncio.Queue) -> None:
        """Lee texto limpio de la cola, lo parsea y lo habla."""
        lexer = self._lexer_class()

        while True:
            chunk = await text_queue.get()

            if self.interrupt_event.is_set():
                lexer.buffer = ""
                lexer.in_code_block = False
                self.interrupt_event.clear()

            chunk_type, content = await lexer.process_token(chunk)

            if chunk_type == "TEXT_CHUNK":
                self.tts.speak(content, self.interrupt_event)
            elif chunk_type == "CODE_BLOCK":
                # En PTY mode los bloques de código se saltan igual que en main.py
                lines = len(content.splitlines())
                summary = f"Bloque de código de {lines} líneas."
                self.tts.speak(summary, self.interrupt_event)
