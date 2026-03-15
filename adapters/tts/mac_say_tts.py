import subprocess
import threading
import time


class MacSayTTS:
    """
    Adaptador de Text-to-Speech nativo de macOS.
    Usa el comando 'say' del sistema operativo.
    Es asquerosamente rústico, pero tiene latencia cero y sirve para validar la arquitectura.
    """

    def __init__(self):
        self.current_process = None

    def speak(self, text: str, interrupt_event: threading.Event):
        """
        Reproduce el texto. Monitorea constatemente el interrupt_event (Barge-in).
        Si el evento se dispara (el usuario habló), mata el proceso de voz al instante.
        """
        # Limpiamos caracteres que puedan romper el comando say de bash
        clean_text = text.replace("'", "").replace('"', "")

        # Eliminamos saltos de línea y dobles espacios que causan pausas raras y cortes en el TTS de Apple
        import re

        clean_text = re.sub(r"\s+", " ", clean_text).strip()

        # Invocamos al sistema operativo SIN BLOQUEAR (Popen)
        # Usamos la voz "Daniel" y aumentamos ligeramente la velocidad (-r 200) para darle más fluidez
        # Puedes cambiar la voz a "Mónica" (es_ES) o "Paulina" (es_MX) si prefieres español nativo.
        self.current_process = subprocess.Popen(
            ["say", "-v", "Daniel", "-r", "200", clean_text]
        )

        # Bucle de monitoreo (El corazón del Barge-in del lado del reproductor)
        while (
            self.current_process.poll() is None
        ):  # Mientras el proceso siga corriendo...
            if interrupt_event.is_set():
                # ¡PUM! El usuario habló. Matamos al parlante de Apple.
                self.current_process.terminate()
                # BORRAMOS EL PRINT para no romper la UI de la terminal
                # print("\n[TTS] 🛑 Audio interrumpido por el usuario (Barge-in ejecutado).")
                break

            # Dormimos 50ms para no freír la CPU con el bucle `while`
            time.sleep(0.05)
