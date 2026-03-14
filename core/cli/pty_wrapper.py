import os
import pty
import tty
import select
import termios
import sys
import fcntl
import struct
import shutil
from typing import Optional


class PtyCLIWrapper:
    """
    Este es el 'Hombre en el Medio' (MitM).
    Lanza una Pseudo-Terminal para engañar a la CLI haciéndole creer
    que está corriendo en la terminal real del usuario.
    """

    def __init__(self, command: list[str]):
        self.command = command
        self.pid: Optional[int] = None
        self.fd: Optional[int] = None  # File Descriptor de nuestra terminal falsa
        self.running = False

    def _sync_terminal_size(self):
        """
        Copia las dimensiones (filas y columnas) de tu terminal real
        usando la librería estándar de Python y empaqueta los bits a mano.
        """
        if self.fd is None:
            return

        try:
            # Obtenemos las columnas y filas reales de tu Mac
            cols, rows = shutil.get_terminal_size(fallback=(80, 24))

            # Empaquetamos en C struct: 4 unsigned shorts (filas, columnas, x_pix, y_pix)
            # Esto es lo que el sistema operativo bajo nivel entiende
            winsize = struct.pack("HHHH", rows, cols, 0, 0)

            # Forzamos a la terminal falsa a adoptar este tamaño
            fcntl.ioctl(self.fd, termios.TIOCSWINSZ, winsize)
        except Exception as e:
            pass

    def start(self):
        """Lanza el proceso enganchado a un PTY."""

        # Obtenemos el tamaño ANTES del fork
        cols, rows = shutil.get_terminal_size(fallback=(80, 24))

        self.pid, self.fd = pty.fork()

        if self.pid == 0:
            # ---> CÓDIGO DEL PROCESO HIJO (Acá corre la CLI de Gemini) <---

            # 1. Le decimos que es una terminal a color
            os.environ["TERM"] = os.environ.get("TERM", "xterm-256color")

            # 2. Le pasamos explícitamente las variables de entorno de tamaño (Obliga a NodeJS/Go a estirarse)
            os.environ["COLUMNS"] = str(cols)
            os.environ["LINES"] = str(rows)

            try:
                os.execvp(self.command[0], self.command)
            except FileNotFoundError:
                print(
                    f"\n[ERROR CRÍTICO] No se encontró el comando '{self.command[0]}'."
                )
                sys.exit(1)
        else:
            # ---> CÓDIGO DEL PROCESO PADRE (Nuestro Wrapper J.A.R.V.I.S.) <---
            self.running = True

            # 3. Sincronizamos el tamaño de la ventana a nivel Kernel (ioctl)
            self._sync_terminal_size()

            self.old_tty = termios.tcgetattr(sys.stdin)
            tty.setraw(sys.stdin.fileno())

    def read_stream_non_blocking(self) -> Optional[str]:
        """Lee bytes de la salida de la CLI sin bloquear."""
        if not self.running or self.fd is None:
            return None

        ready_to_read, _, _ = select.select([self.fd], [], [], 0.1)

        if self.fd in ready_to_read:
            try:
                data = os.read(self.fd, 1024)
                if not data:
                    self.running = False
                    return None
                return data.decode("utf-8", errors="ignore")
            except OSError:
                self.running = False
                return None
        return None

    def send_input(self, text: str):
        """Escribe texto en la entrada de la CLI."""
        if self.running and self.fd is not None:
            os.write(self.fd, (text + "\n").encode("utf-8"))

    def stop(self):
        """Mata al proceso hijo y restaura la terminal."""
        self.running = False
        if self.pid:
            try:
                os.kill(self.pid, 9)
            except OSError:
                pass
        if hasattr(self, "old_tty"):
            termios.tcsetattr(sys.stdin, termios.TCSADRAIN, self.old_tty)
