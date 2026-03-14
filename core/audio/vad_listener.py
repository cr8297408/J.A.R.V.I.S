import pyaudio
import numpy as np
import threading
import logging
import wave
import subprocess
import webrtcvad
from openwakeword.model import Model
from adapters.stt.mlx_stt import LocalSTT
from adapters.stt.ghost_typer import GhostTyper

awaiting_tool_permission = threading.Event()


def play_sfx(sound_name):
    """Reproduce sonidos nativos de Mac para feedback no bloqueante."""
    sounds = {
        "wake": "/System/Library/Sounds/Ping.aiff",
        "stop": "/System/Library/Sounds/Pop.aiff",
        "error": "/System/Library/Sounds/Basso.aiff",
    }
    path = sounds.get(sound_name)
    if path:
        subprocess.Popen(["afplay", path])


def start_vad_thread(interrupt_event: threading.Event):
    """
    Máquina de estados de Escucha Activa:
    1. Espera 'Hey Jarvis' (Wake Word).
    2. Graba el comando del usuario hasta detectar silencio (VAD).
    3. Transcribe usando MLX Whisper.
    4. Inyecta el texto en la terminal.
    """

    def listener():
        logging.info("Inicializando Pipeline de Escucha Activa...")

        # 1. Cargar Modelos
        try:
            # Los modelos ahora están descargados correctamente dentro del paquete de openwakeword
            owwModel = Model(wakeword_models=["hey_jarvis"], inference_framework="onnx")
            stt_engine = LocalSTT()
            vad = webrtcvad.Vad(2)  # Agresividad media (0-3) para detectar silencio
        except Exception as e:
            logging.error(f"Fallo cargando modelos: {e}")
            return

        audio = pyaudio.PyAudio()
        FORMAT = pyaudio.paInt16
        CHANNELS = 1
        RATE = 16000

        # OWW necesita 1280 (80ms), WebRTCVAD necesita frames exactos de 10, 20 o 30ms.
        # 480 frames a 16kHz = 30ms. Usaremos 480 como base común y acumularemos para OWW.
        CHUNK = 480

        stream = None
        try:
            stream = audio.open(
                format=FORMAT,
                channels=CHANNELS,
                rate=RATE,
                input=True,
                frames_per_buffer=CHUNK,
            )

            logging.info("Jarvis en Standby. Esperando 'Hey Jarvis'...")

            # Variables de Estado
            state = "WAITING_WAKEWORD"
            frames_buffer = []  # Para acumular hasta los 1280 que necesita OWW
            recording_frames = []  # Para guardar el comando entero
            silence_chunks = 0
            MAX_SILENCE_CHUNKS = 50  # ~1.5 segundos de silencio a 30ms por chunk

            while True:
                raw_audio = stream.read(CHUNK, exception_on_overflow=False)

                if state == "WAITING_WAKEWORD":
                    if awaiting_tool_permission.is_set():
                        logging.info("Auto-triggering recording for tool permission...")
                        play_sfx("wake")
                        owwModel.reset()
                        state = "RECORDING_COMMAND"
                        recording_frames = []
                        silence_chunks = 0
                        frames_buffer = []
                        continue

                    frames_buffer.append(raw_audio)
                    # OWW espera chunks de ~1280 (nosotros acumulamos 3 * 480 = 1440)
                    if len(frames_buffer) >= 3:
                        combined_audio = b"".join(frames_buffer)
                        audio_data = np.frombuffer(combined_audio, dtype=np.int16)

                        prediction = owwModel.predict(audio_data)

                        for mdl in list(owwModel.prediction_buffer.keys()):
                            score = (
                                prediction[mdl] if isinstance(prediction, dict) else 0.0
                            )

                            # Ajuste de Sensibilidad: Bajamos el threshold de 0.5 a 0.35
                            # para que reconozca el acento en español y variaciones más fácil
                            if score > 0.35:
                                logging.info(
                                    f"¡Wake Word detectada! (Score: {score:.2f})"
                                )
                                # 1. Callar si estaba hablando
                                if not interrupt_event.is_set():
                                    interrupt_event.set()

                                # 2. Feedback sonoro
                                play_sfx("wake")

                                # 3. Cambiar de estado
                                owwModel.reset()
                                state = "RECORDING_COMMAND"
                                recording_frames = []
                                silence_chunks = 0
                                break  # Salir del for loop

                        frames_buffer = []  # Limpiar buffer corto

                elif state == "RECORDING_COMMAND":
                    recording_frames.append(raw_audio)

                    # Chequear silencio con WebRTCVAD
                    is_speech = vad.is_speech(raw_audio, RATE)
                    if not is_speech:
                        silence_chunks += 1
                    else:
                        silence_chunks = 0  # Resetear si detecta voz

                    # Si detectó ~1.5s de silencio, termina de grabar
                    if silence_chunks > MAX_SILENCE_CHUNKS:
                        logging.info("Silencio detectado. Procesando comando...")
                        play_sfx("stop")
                        state = "PROCESSING"

                        # Guardar a WAV temporal
                        temp_wav = "temp_command.wav"
                        with wave.open(temp_wav, "wb") as wf:
                            wf.setnchannels(CHANNELS)
                            wf.setsampwidth(audio.get_sample_size(FORMAT))
                            wf.setframerate(RATE)
                            wf.writeframes(b"".join(recording_frames))

                        # Capturar si era una respuesta a un tool permission antes de limpiar
                        was_tool_permission = awaiting_tool_permission.is_set()
                        if was_tool_permission:
                            awaiting_tool_permission.clear()

                        # Transcribir en un hilo separado para no bloquear la lectura del mic
                        def transcribe_and_type(is_tool: bool):
                            text = stt_engine.transcribe(temp_wav)
                            if text:
                                logging.info(f"Comando transcrito: {text}")
                                if is_tool:
                                    t_lower = text.lower()
                                    if any(
                                        w in t_lower
                                        for w in [
                                            "once",
                                            "una vez",
                                            "1",
                                            "one",
                                            "uno",
                                            "yes",
                                            "sí",
                                            "si",
                                        ]
                                    ):
                                        GhostTyper.type_string("1")
                                    elif any(
                                        w in t_lower
                                        for w in [
                                            "session",
                                            "sesión",
                                            "2",
                                            "two",
                                            "dos",
                                            "siempre",
                                            "always",
                                        ]
                                    ):
                                        GhostTyper.type_string("2")
                                    elif any(
                                        w in t_lower
                                        for w in [
                                            "deny",
                                            "denegar",
                                            "no",
                                            "3",
                                            "three",
                                            "tres",
                                        ]
                                    ):
                                        GhostTyper.type_string("3")
                                    else:
                                        GhostTyper.type_string(text)
                                else:
                                    GhostTyper.type_string(text)
                            else:
                                play_sfx("error")

                        threading.Thread(
                            target=transcribe_and_type, args=(was_tool_permission,)
                        ).start()

                        # Volver a Standby
                        state = "WAITING_WAKEWORD"
                        frames_buffer = []

        except Exception as e:
            logging.error(f"[VAD LISTENER ERROR] {e}")
        finally:
            if stream is not None:
                stream.stop_stream()
                stream.close()
            audio.terminate()

    t = threading.Thread(target=listener, daemon=True)
    t.start()
    return t
