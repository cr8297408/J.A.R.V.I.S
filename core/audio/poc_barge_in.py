import pyaudio
import webrtcvad
import threading
import time

# Configuraciones de Audio (Magia Negra de Procesamiento de Señales)
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 16000
# WebRTCVAD exige frames de 10, 20 o 30 ms.
# 30 ms * 16 kHz = 480 muestras. Cada muestra es Int16 (2 bytes) = 960 bytes por frame.
FRAME_DURATION_MS = 30
CHUNK = int(RATE * FRAME_DURATION_MS / 1000)

# Evento Thread-safe para la interrupción
interrupt_event = threading.Event()


def dummy_tts_player():
    """Simula la reproducción de voz. Tarda 10 segundos, a menos que lo interrumpan."""
    print("\n[J.A.R.V.I.S.] Empezando a hablar una respuesta re larga... (10 segundos)")
    for i in range(100):
        # El corazón del "Barge-in": Chequear la bandera de interrupción en CADA ITERACIÓN
        if interrupt_event.is_set():
            print("\n[J.A.R.V.I.S.] ¡OK OK, ME CALLO LA BOCA! (Barge-in exitoso) 🛑")
            break

        # Simula que está reproduciendo 0.1s de audio...
        print("bla ", end="", flush=True)
        time.sleep(0.1)

    print("\n[J.A.R.V.I.S.] Hilo de reproducción terminado.")


def microphone_listener():
    """Escucha el micrófono constantemente en un hilo separado y detecta voz (VAD)."""
    vad = webrtcvad.Vad(
        3
    )  # Nivel de agresividad (0-3). 3 es el más estricto filtrando ruido.
    audio = pyaudio.PyAudio()

    stream = audio.open(
        format=FORMAT, channels=CHANNELS, rate=RATE, input=True, frames_per_buffer=CHUNK
    )

    print("\n[MIC] Hilo de escucha iniciado. Monitoreando silencio...")

    consecutive_voice_frames = 0
    REQUIRED_FRAMES = 5  # Cuántos frames (de 30ms) seguidos tienen que ser voz para no saltar por un ruido falso

    try:
        while True:
            # Leemos 960 bytes crudos de la placa de sonido de tu Mac
            frame = stream.read(CHUNK, exception_on_overflow=False)

            # Pasamos los bytes crudos por el motor de WebRTCVAD
            is_speech = vad.is_speech(frame, RATE)

            if is_speech:
                consecutive_voice_frames += 1
            else:
                consecutive_voice_frames = 0

            # Si detectamos que estás hablando de verdad...
            if consecutive_voice_frames >= REQUIRED_FRAMES:
                print("\n\n[MIC] 🎙️ ¡VOZ DETECTADA! Disparando interrupción...")
                interrupt_event.set()
                # Rompemos el bucle de escucha por ahora (en el sistema real, pasaría a modo "Grabando")
                break

    except Exception as e:
        print(f"Error en el mic: {e}")
    finally:
        stream.stop_stream()
        stream.close()
        audio.terminate()


def main():
    print("=== Iniciando Prueba de Concepto de Barge-in ===")

    # Creamos los dos hilos (Threads) independientes
    mic_thread = threading.Thread(target=microphone_listener, daemon=True)
    player_thread = threading.Thread(target=dummy_tts_player)

    # Arrancamos los motores
    mic_thread.start()
    time.sleep(1)  # Le damos un segundito al mic para calentar motores

    # J.A.R.V.I.S empieza a hablar...
    player_thread.start()

    # Esperamos a que los hilos terminen
    player_thread.join()

    print("\n=== PoC Finalizada ===")


if __name__ == "__main__":
    main()
