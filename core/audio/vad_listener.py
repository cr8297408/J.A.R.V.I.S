import pyaudio
import numpy as np
import sys
import threading
import logging
import wave
import subprocess
import webrtcvad
import asyncio
import unicodedata
from openwakeword.model import Model
from adapters.stt.ghost_typer import GhostTyper


def _normalize(text: str) -> str:
    """Minúsculas + strip acentos + eliminar puntuación básica. Usado para el filtro de alucinaciones."""
    text = text.lower().strip()
    text = text.replace("!", "").replace("¡", "").replace(".", "").replace(",", "").replace("?", "").replace("¿", "")
    # Descomponer caracteres Unicode y quedarse solo con ASCII (elimina acentos)
    return unicodedata.normalize("NFD", text).encode("ascii", "ignore").decode("ascii")

active_listening_requested = threading.Event()
jarvis_speaking = threading.Event()

# Contexto global para compartir con el demonio
user_context = {"last_command": "", "last_speech": "", "last_terminal_output": ""}


def play_sfx(sound_name: str) -> None:
    """Reproduce feedback sonoro no bloqueante. Solo en macOS (afplay)."""
    if sys.platform != "darwin":
        return
    sounds = {
        "wake": "/System/Library/Sounds/Ping.aiff",
        "stop": "/System/Library/Sounds/Pop.aiff",
        "error": "/System/Library/Sounds/Basso.aiff",
    }
    path = sounds.get(sound_name)
    if path:
        subprocess.Popen(["afplay", path])


def start_vad_thread(
    interrupt_event: threading.Event,
    summarizer=None,
    tts=None,
    loop=None,
    on_transcription=None,
):
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
            from core.platform_utils import get_stt_class
            stt_engine = get_stt_class()()
            vad = webrtcvad.Vad(3)  # Agresividad MÁXIMA (3) para ignorar ruido de fondo
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
            MAX_RECORDING_CHUNKS = (
                2000  # ~15 segundos máximo absoluto (500 * 30ms = 15s)
            )
            MIN_RMS_THRESHOLD = (
                450  # Umbral de volumen para ignorar ruido de fondo bajo
            )

            while True:
                raw_audio = stream.read(CHUNK, exception_on_overflow=False)

                if state == "WAITING_WAKEWORD":
                    # Solo activar el auto-trigger DESPUÉS de que Jarvis termine de hablar.
                    # Si está activo mientras jarvis_speaking está seteado, el mic graba el
                    # audio del altavoz (echo del TTS) y lo transcribe como un comando.
                    if active_listening_requested.is_set() and not jarvis_speaking.is_set():
                        logging.info("Auto-triggering recording for follow-up...")
                        play_sfx("wake")
                        owwModel.reset()
                        active_listening_requested.clear()
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
                    # Si Jarvis está hablando, descartamos los frames acumulados.
                    # Así evitamos que el eco del altavoz quede grabado y sea
                    # transcripto como si fuera el usuario hablando.
                    if jarvis_speaking.is_set():
                        recording_frames = []
                        silence_chunks = 0
                        continue

                    recording_frames.append(raw_audio)

                    # 1. Calcular volumen (RMS) del chunk actual
                    audio_data_chunk = np.frombuffer(raw_audio, dtype=np.int16)
                    rms = np.sqrt(
                        np.mean(np.square(audio_data_chunk.astype(np.float32)))
                    )

                    # 2. Chequear silencio con WebRTCVAD
                    is_speech = vad.is_speech(raw_audio, RATE)

                    # Si VAD dice que es silencio, o el volumen es demasiado bajo (ruido de fondo)
                    if not is_speech or rms < MIN_RMS_THRESHOLD:
                        # Si Jarvis está hablando, NO incrementamos el silencio (mantenemos el mic abierto)
                        if not jarvis_speaking.is_set():
                            silence_chunks += 1
                    else:
                        silence_chunks = 0  # Resetear si detecta voz real

                    # Si detectó ~1.5s de silencio o pasamos el límite absoluto de tiempo
                    if (
                        silence_chunks > MAX_SILENCE_CHUNKS
                        or len(recording_frames) > MAX_RECORDING_CHUNKS
                    ):
                        if len(recording_frames) > MAX_RECORDING_CHUNKS:
                            logging.info(
                                "Límite máximo de grabación (15s) alcanzado. Cortando..."
                            )
                        else:
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
                        was_active_listening = active_listening_requested.is_set()
                        if was_active_listening:
                            active_listening_requested.clear()

                        # Transcribir en un hilo separado para no bloquear la lectura del mic
                        def transcribe_and_type():
                            text = stt_engine.transcribe(temp_wav)
                            if not text:
                                return

                            logging.info(f"Voz detectada: {text}")
                            
                            # Filtro de alucinaciones comunes de Whisper en silencio/ruido.
                            # _normalize() elimina acentos para que "¡Suscríbete!" == "suscribete".
                            t_clean = _normalize(text)
                            if t_clean in ["suscribete", "subscribete", "gracias por ver", "gracias", "watching", "subtitulos por", "transcrito por"]:
                                logging.info(f"Hallucination filtrada: {text}")
                                return

                            user_context["last_command"] = text

                            # Modo API: callback directo, sin GhostTyper ni PTY
                            if on_transcription is not None:
                                on_transcription(text)
                                return

                            # Modo PTY: evaluación inteligente con el summarizer
                            if (
                                summarizer
                                and loop
                                and hasattr(summarizer, "evaluate_response")
                            ):
                                logging.info("Evaluando respuesta con J.A.R.V.I.S...")
                                try:
                                    future = asyncio.run_coroutine_threadsafe(
                                        summarizer.evaluate_response(text, user_context),
                                        loop,
                                    )
                                    decision = future.result(timeout=10.0)

                                    action = decision.get("action", "type")
                                    value = decision.get("value", text)
                                    reasoning = decision.get("reasoning", "Sin razonamiento")
                                    logging.info(f"[Cerebro Jarvis] {reasoning} -> {action}")

                                    if action == "authorize":
                                        # Verificar que el permiso no haya expirado.
                                        # Si pasaron más de 90s desde que llegó la notificación,
                                        # Gemini ya procesó o descartó el permiso — no enviamos "1".
                                        import time as _time
                                        pending_ts = user_context.get("pending_permission_ts")
                                        PERMISSION_TIMEOUT_SECS = 90
                                        if pending_ts and (_time.monotonic() - pending_ts) > PERMISSION_TIMEOUT_SECS:
                                            logging.warning(
                                                f"Aprobación tardía descartada — "
                                                f"{_time.monotonic() - pending_ts:.0f}s desde el permiso (límite {PERMISSION_TIMEOUT_SECS}s). "
                                                "Gemini ya procesó o descartó la solicitud."
                                            )
                                            # TODO: notificar al usuario por TTS que llegó tarde
                                        else:
                                            user_context["pending_permission_ts"] = None
                                            GhostTyper.type_string(value if value else "1")
                                    elif action == "type":
                                        GhostTyper.type_string(value if value else text)
                                    elif action == "answer":
                                        # El usuario hace una pregunta → va al terminal para que el LLM responda.
                                        GhostTyper.type_string(text)
                                    elif action == "ignore":
                                        logging.info("Entrada ignorada.")
                                    else:
                                        logging.info(f"Acción desconocida '{action}' — ignorando para no contaminar el terminal.")
                                except Exception as e:
                                    logging.error(f"Error evaluando respuesta: {e}")
                                    GhostTyper.type_string(text)
                            else:
                                GhostTyper.type_string(text)

                        threading.Thread(target=transcribe_and_type).start()

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
