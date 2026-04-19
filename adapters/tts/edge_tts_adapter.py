import subprocess
import threading
import time
import os
import re
import uuid
import sys


class EdgeTTS:
    """
    Adaptador de Text-to-Speech usando voces neuronales de Edge TTS (Microsoft).
    Es completamente gratuito, sin API keys y suena extremadamente realista.
    """

    def __init__(self):
        self.current_process = None
        # Voces recomendadas:
        # "es-ES-AlvaroNeural" (Español de España, muy claro y profesional, tipo Jarvis)
        # "es-MX-JorgeNeural" (Español de México, un poco más neutro/latino)
        self.voice = "es-ES-AlvaroNeural"

    def speak(self, text: str, interrupt_event: threading.Event):
        """
        Genera el audio con Edge TTS y lo reproduce.
        Monitorea constatemente el interrupt_event (Barge-in).
        """
        if not text or not text.strip():
            return

        # Limpiamos el texto
        clean_text = text.replace("'", "").replace('"', "")
        clean_text = re.sub(r"\s+", " ", clean_text).strip()

        # Nombre de archivo temporal único para evitar colisiones si se llama rápido varias veces
        temp_file = f"temp_speech_{uuid.uuid4().hex[:8]}.mp3"

        # 1. Generar el archivo MP3
        try:
            # Usar sys.executable asegura que usemos el mismo python del entorno virtual
            subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "edge_tts",
                    "--voice",
                    self.voice,
                    "--text",
                    clean_text,
                    "--write-media",
                    temp_file,
                ],
                check=True,
                capture_output=True,
            )
        except subprocess.CalledProcessError as e:
            error_output = (
                e.stderr.decode("utf-8", errors="ignore") if e.stderr else str(e)
            )
            print(f"Error generando TTS con Edge: {error_output}")
            return
        except Exception as e:
            print(f"Error inesperado generando TTS: {e}")
            return

        # Si el usuario habló mientras se generaba, abortamos antes de reproducir
        if interrupt_event.is_set():
            if os.path.exists(temp_file):
                os.remove(temp_file)
            return

        # 2. Reproducir el archivo generado con el player disponible en la plataforma
        from core.platform_utils import get_audio_player_cmd
        self.current_process = subprocess.Popen(get_audio_player_cmd(temp_file))

        # Bucle de monitoreo (El corazón del Barge-in del lado del reproductor)
        while self.current_process.poll() is None:
            if interrupt_event.is_set():
                # ¡PUM! El usuario habló. Matamos al reproductor.
                self.current_process.terminate()
                break

            time.sleep(0.05)

        # 3. Limpiar el archivo temporal
        if os.path.exists(temp_file):
            try:
                os.remove(temp_file)
            except:
                pass
