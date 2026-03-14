import pyaudio
import webrtcvad
import threading


def start_vad_thread(interrupt_event: threading.Event):
    """
    Inicia un hilo demonio que monitorea el micrófono constantemente.
    Si detecta voz continua, dispara el evento de interrupción (Barge-in).
    """

    def listener():
        vad = webrtcvad.Vad(3)
        audio = pyaudio.PyAudio()

        try:
            stream = audio.open(
                format=pyaudio.paInt16,
                channels=1,
                rate=16000,
                input=True,
                frames_per_buffer=480,
            )  # 30ms a 16kHz

            consecutive_voice_frames = 0

            while True:
                frame = stream.read(480, exception_on_overflow=False)
                is_speech = vad.is_speech(frame, 16000)

                if is_speech:
                    consecutive_voice_frames += 1
                else:
                    consecutive_voice_frames = 0

                # Si hay voz sostenida (aprox 150ms)
                if consecutive_voice_frames >= 5:
                    # Solo disparamos si no estaba ya disparado
                    if not interrupt_event.is_set():
                        interrupt_event.set()
                    consecutive_voice_frames = 0  # Reseteamos para la próxima

        except Exception as e:
            print(f"\n[VAD ERROR] {e}")
        finally:
            stream.stop_stream()
            stream.close()
            audio.terminate()

    t = threading.Thread(target=listener, daemon=True)
    t.start()
    return t
