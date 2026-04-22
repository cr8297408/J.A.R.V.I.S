"""
Jarvis — Entry point PTY.

Dispatcher de modos: lanza la sesión correcta según el argumento.

Uso:
    python main.py              → modo coding (OpenCode + Ollama, default)
    python main.py --mode code  → modo coding
    python main.py --mode api   → modo API daemon (jarvis_daemon.py)

El modo coding usa OpenCodePtySession, que ya integra:
    - VAD + Whisper (escucha de voz)
    - OllamaAdapter (cerebro summarizer)
    - PTY wrapper de OpenCode
    - TTS (mac_say)

Para el modo completo con PC control, usar el daemon:
    python core/server/jarvis_daemon.py
"""
import sys
import os
import argparse

sys.path.append(os.path.dirname(os.path.abspath(__file__)))


def run_coding_mode():
    """Lanza Jarvis en modo coding: OpenCode + Ollama via PTY."""
    from core.session.opencode_pty_session import OpenCodePtySession
    session = OpenCodePtySession()
    session.run()


def run_daemon_mode():
    """Lanza el daemon completo con los tres modos (general, PC, coding)."""
    from core.server import jarvis_daemon
    jarvis_daemon.main()


def main():
    parser = argparse.ArgumentParser(
        description="J.A.R.V.I.S — Asistente de voz 100% local con Gemma 4"
    )
    parser.add_argument(
        "--mode",
        choices=["code", "api", "daemon"],
        default="code",
        help=(
            "code: OpenCode + Ollama via PTY (default). "
            "daemon/api: servidor completo con tres modos (general, PC, coding)."
        ),
    )
    args = parser.parse_args()

    if args.mode == "code":
        run_coding_mode()
    else:
        run_daemon_mode()


if __name__ == "__main__":
    main()
