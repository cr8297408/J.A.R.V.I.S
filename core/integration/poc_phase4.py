import sys
import os
import time
import select
import tty
import termios

# Agregamos la ruta base
sys.path.append(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)

from core.cli.pty_wrapper import PtyCLIWrapper


def main():
    wrapper = PtyCLIWrapper(["gemini"])

    print(
        "\r\n[J.A.R.V.I.S] Inicializando Pseudo-Terminal para secuestrar a Gemini...\r\n"
    )

    # Guardamos los settings del teclado ORIGINAL para no romperte la terminal si algo falla
    try:
        old_tty = termios.tcgetattr(sys.stdin.fileno())
    except Exception:
        old_tty = None

    try:
        wrapper.start()

        # Ponemos el teclado en modo raw
        tty.setraw(sys.stdin.fileno())

        while wrapper.running and wrapper.fd is not None:
            rlist, _, _ = select.select([sys.stdin, wrapper.fd], [], [], 0.05)

            # Caso 1: El usuario apretó una tecla
            if sys.stdin in rlist:
                char = os.read(sys.stdin.fileno(), 1)
                if not char:
                    break

                # Si apretó Ctrl+C (código ASCII 3)
                if char == b"\x03":
                    raise KeyboardInterrupt

                os.write(wrapper.fd, char)

            # Caso 2: Gemini escupió una respuesta
            if wrapper.fd in rlist:
                chunk = wrapper.read_stream_non_blocking()
                if chunk:
                    sys.stdout.write(chunk)
                    sys.stdout.flush()

    except KeyboardInterrupt:
        pass
    finally:
        if old_tty:
            termios.tcsetattr(sys.stdin.fileno(), termios.TCSADRAIN, old_tty)
        wrapper.stop()
        print(
            "\r\n[J.A.R.V.I.S] Wrapper PTY cerrado limpiamente. Terminal restaurada.\r\n"
        )


if __name__ == "__main__":
    main()
