"""
OpenCodePtySession — PTY wrapper para OpenCode CLI.

Mismo patrón que ClaudeCodePtySession, adaptado al TUI de OpenCode.
OpenCode es un agente de coding open-source con soporte nativo de Ollama.

Repositorio: https://github.com/sst/opencode
Instalación: brew install sst/tap/opencode  (Mac)
             Ver releases para Windows/Linux

Configuración de Ollama en OpenCode (~/.config/opencode/config.json):
    {
      "providers": { "ollama": { "models": ["qwen2.5-coder:7b", "gemma4:latest"] } },
      "model": "ollama/qwen2.5-coder:7b"
    }

Flujo:
    User speaks → VAD → Whisper → GhostTyper → PTY(opencode) → TUI filter → TTS
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

# ── Limpieza de terminal ──────────────────────────────────────────────────────

ANSI_CLEANER    = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")
BOX_CLEANER     = re.compile(
    r"[─━│┃┄┅┆┇┈┉┊┋┌┍┎┏┐┑┒┓└┕┖┗┘┙┚┛├┝┞┟┠┡┢┣┤┥┦┧┨┩┪┫┬┭┮┯┰┱┲┳┴┵┶┷┸┹┺┻┼┽┾┿╀╁╂╃╄╅╆╇╈╉╊╋═║╒╓╔╕╖╗╘╙╚╛╜╝╞╟╠╡╢╣╤╥╦╧╨╩╪╫╬╭╮╯╰╱╲╳╴╵╶╷╸╹╺╻╼╽╾╿▀▂▃▄▅▆▇█▉▊▋▌▍▎▏▐░▒▓▔▕▖▗▘▙▚▛▜▝▞▟]+"
)
TITLE_CLEANER   = re.compile(r"\x1b\]0;.*?\x07")
SPINNER_CLEANER = re.compile(r"[⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏⣾⣽⣻⢿⡿⣟⣯⣷]+")

# ── Filtros específicos del TUI de OpenCode ───────────────────────────────────
# OpenCode usa Bubble Tea (Go TUI). Estos artefactos aparecen en su output.
# Se completan/refinan al testear el TUI real.

TUI_BLACKLIST = [
    # Header y branding
    "opencode",
    "OpenCode",
    # Info de modelo y sesión
    "model:",
    "provider:",
    "session:",
    # Contadores de tokens y costo
    "tokens",
    "prompt tokens",
    "completion tokens",
    "total tokens",
    # Estados de herramientas
    "Running tool",
    "Tool call",
    "Tool result",
    "bash(",
    "read_file(",
    "write_file(",
    "list_directory(",
    "search_files(",
    # Shortcuts de teclado (status bar)
    "ctrl+c",
    "ctrl+d",
    "esc",
    "enter",
    # Spinner y estados de carga
    "thinking",
    "Thinking",
    # Prompt vacío
    "❯",
    "›",
]


def clean_tui_chunk(raw_chunk: str) -> str:
    """
    Limpia el output crudo del TUI de OpenCode para que sea legible por TTS.
    Mismo patrón que ClaudeCodePtySession pero con blacklist de OpenCode.
    """
    normalized = raw_chunk.replace("\r\n", "\n").replace("\r", "\n")
    lines = normalized.split("\n")
    valid_lines = []

    for line in lines:
        clean = ANSI_CLEANER.sub("", line)

        # Descartar líneas con artefactos del TUI
        if any(bad in clean for bad in TUI_BLACKLIST):
            continue

        # Descartar líneas que son solo el directorio actual
        if os.path.basename(os.getcwd()) in clean and len(clean.strip()) < 60:
            continue

        clean = BOX_CLEANER.sub("", clean)
        clean = TITLE_CLEANER.sub("", clean)
        clean = SPINNER_CLEANER.sub("", clean)

        # Limpiar decoradores comunes de TUI Go
        clean = clean.replace("✓", "").replace("✗", "").replace("●", "")
        clean = clean.replace("○", "").replace("►", "").replace("▶", "")
        clean = clean.strip()

        if len(clean) < 2 and clean in ("", ">", "$", "❯", "›"):
            continue

        valid_lines.append(clean)

    return " ".join(valid_lines).strip()


# ── Sesión PTY ────────────────────────────────────────────────────────────────

class OpenCodePtySession:
    """
    Wrapper PTY para OpenCode CLI con overlay de voz.

    Activa el modo coding de Jarvis: comandos de voz → OpenCode → TTS.
    OpenCode usa Ollama localmente — cero API keys, cero costo.

    Uso:
        session = OpenCodePtySession()
        session.run()  # bloqueante hasta Ctrl+C o "salir del modo código"
    """

    def __init__(self) -> None:
        from adapters.tts.mac_say_tts import MacSayTTS
        from adapters.llm.ollama_adapter import OllamaAdapter, CODE_MODEL
        from core.lexer.poc_lexer import StreamingLexer

        self.tts = MacSayTTS()
        self.brain = OllamaAdapter(model=CODE_MODEL)
        self.interrupt_event = threading.Event()
        self._lexer_class = StreamingLexer

    def run(self) -> None:
        """Inicia la sesión PTY de OpenCode. Bloqueante hasta Ctrl+C."""
        from core.cli.pty_wrapper import PtyCLIWrapper
        from core.audio.vad_listener import start_vad_thread

        print("\r\n[J.A.R.V.I.S] Modo Coding — OpenCode con Ollama. Inicializando...\r\n")
        self._check_opencode_available()

        brain_loop = asyncio.new_event_loop()
        text_queue: asyncio.Queue = asyncio.Queue()

        threading.Thread(
            target=self._brain_thread,
            args=(text_queue, brain_loop),
            daemon=True,
        ).start()

        start_vad_thread(self.interrupt_event)

        wrapper = PtyCLIWrapper(["opencode"])

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

                if sys.stdin in rlist:
                    char = os.read(sys.stdin.fileno(), 1)
                    if not char:
                        break
                    if char == b"\x03":
                        raise KeyboardInterrupt
                    if char in (b"\r", b"\n"):
                        is_user_typing = False
                        self.interrupt_event.set()
                    else:
                        is_user_typing = True
                        self.interrupt_event.set()
                    os.write(wrapper.fd, char)

                if wrapper.fd in rlist:
                    chunk = wrapper.read_stream_non_blocking()
                    if chunk:
                        sys.stdout.write(chunk)
                        sys.stdout.flush()

                        if is_user_typing:
                            continue

                        clean = clean_tui_chunk(chunk)
                        if clean:
                            brain_loop.call_soon_threadsafe(text_queue.put_nowait, clean)

        except KeyboardInterrupt:
            logger.info("Sesión OpenCode terminada por el usuario.")
        finally:
            if old_tty:
                termios.tcsetattr(sys.stdin.fileno(), termios.TCSADRAIN, old_tty)
            wrapper.stop()

    def _brain_thread(
        self,
        text_queue: asyncio.Queue,
        loop: asyncio.AbstractEventLoop,
    ) -> None:
        asyncio.set_event_loop(loop)
        loop.run_until_complete(self._brain_async_loop(text_queue))

    async def _brain_async_loop(self, text_queue: asyncio.Queue) -> None:
        """Lee texto limpio de la cola y lo narra por TTS vía OllamaAdapter."""
        lexer = self._lexer_class()
        last_user_command = ""

        while True:
            chunk = await text_queue.get()

            if self.interrupt_event.is_set():
                lexer.buffer = ""
                lexer.in_code_block = False
                self.interrupt_event.clear()

            chunk_type, content = await lexer.process_token(chunk)

            if chunk_type == "TEXT_CHUNK" and content:
                result = await self.brain.summarize(content, user_command=last_user_command)
                if result.get("should_speak") and result.get("speech_content"):
                    self.tts.speak(result["speech_content"], self.interrupt_event)

            elif chunk_type == "CODE_BLOCK" and content:
                lines = len(content.splitlines())
                self.tts.speak(
                    f"Señor, bloque de código de {lines} líneas generado.",
                    self.interrupt_event,
                )

    @staticmethod
    def _check_opencode_available() -> None:
        """Avisa si opencode no está instalado — no crashea, solo informa."""
        import shutil
        if not shutil.which("opencode"):
            print(
                "\r\n[AVISO] 'opencode' no encontrado en el PATH.\r\n"
                "Instalá con: brew install sst/tap/opencode\r\n"
                "O descargá el binario en: github.com/sst/opencode/releases\r\n"
            )
