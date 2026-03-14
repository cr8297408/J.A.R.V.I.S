# Especificación Técnica y Arquitectura
**Nombre del Proyecto:** Gemini Voice CLI Extension (Codename: J.A.R.V.I.S.)
**Arquitecto:** El guacho que te caga a pedos pero te hace programar bien.
**Lenguaje Principal (Mandated by Architect):** Python 3.10+ (Por madurez en ecosistema de audio, VAD e IA local).

## 1. Diseño Arquitectónico (Arquitectura Hexagonal)
No vamos a acoplar la lógica de negocio con las librerías de mierda que cambian cada dos meses. Todo el core se comunica con el mundo exterior mediante **Puertos** (Interfaces) y **Adaptadores** (Patrón Strategy).

### 1.1. Core System (El Cerebro)
- **Máquina de Estados Finita (FSM):** Maneja el flujo del asistente.
  - `IDLE`: Esperando que hables.
  - `LISTENING`: Grabando audio del micrófono.
  - `THINKING`: Transcribiendo (STT) y pegándole a Gemini.
  - `SUMMARIZING`: Pasando el output crudo de Gemini por un LLM rápido para hacerlo conversacional.
  - `SPEAKING`: Reproduciendo el resumen (TTS).
  - `WAITING_APPROVAL`: Estado bloqueante si Gemini generó una acción destructiva (ej: guardar archivo, correr comando).

### 1.2. Puertos y Adaptadores (Strategy Pattern)

#### A. STT (Speech-to-Text) Engine
- **Puerto:** `ISpeechRecognizer.transcribe(audio_stream: bytes) -> str`
- **Adaptadores:**
  - `LocalWhisperAdapter`: Usa `faster-whisper` (CTranslate2) corriendo en CPU o GPU local.
  - `OpenAIWhisperAdapter`: Le pega a la API de OpenAI.

#### B. TTS (Text-to-Speech) Engine
- **Puerto:** `ITextToSpeech.synthesize(text: str) -> bytes`
- **Adaptadores:**
  - `LocalPiperAdapter`: Usa Piper TTS (ONNX) para síntesis local ultrarrápida.
  - `ElevenLabsAdapter`: Le pega a la API de ElevenLabs vía WebSocket para baja latencia.

#### C. Lógica de Intermediación (Gemini Proxy)
- **Función:** Captura la respuesta final de Gemini CLI antes de imprimirla en pantalla.
- **Flujo:** `Raw_Gemini_Output -> LLM_Summarizer_Prompt -> Conversational_Output -> TTS`

## 2. El Problema del Barge-in (Interrupción)
Este es el quilombo más grande de ingeniería del proyecto. No podés tener un hilo bloqueado reproduciendo audio y esperar que escuche al mismo tiempo.

### 2.1. Arquitectura de Hilos (Threading)
- **Main Thread:** Maneja la FSM y la UI de la terminal (logs, spinners).
- **Audio Output Thread:** Se encarga de bufferear y reproducir el TTS. Debe aceptar señales de cancelación (`Event.set()`).
- **Microphone Listener Thread:** Corre constantemente. Usa **Silero VAD** (Voice Activity Detection).
  - Si el VAD detecta silencio, asume que terminaste de hablar y manda el audio al STT.
  - Si el VAD detecta que empezaste a hablar MIENTRAS el estado es `SPEAKING`, dispara un evento `INTERRUPT_SIGNAL`. El Audio Output Thread agarra la señal, frena la reproducción (vacía el buffer de PyAudio) y cambia el estado a `LISTENING`.

## 3. Tech Stack Recomendado (Python)
- **Audio I/O:** `pyaudio` o `sounddevice`.
- **VAD (Voice Activity Detection):** `silero-vad` (Torch) o `webrtcvad`.
- **STT Local:** `faster-whisper`.
- **TTS Local:** `piper-tts` o `coqui-tts`.
- **Clientes Remotos:** `openai`, `elevenlabs`.
- **LLM/Orquestación:** Llamadas directas a la API de `google-generativeai` (Gemini).

## 4. Estructura de Directorios Propuesta
```text
├── core/
│   ├── fsm.py          # Máquina de estados
│   ├── orchestrator.py # Lógica principal
│   └── summarizer.py   # El prompt que resume la salida de Gemini
├── adapters/
│   ├── stt/            # LocalWhisper, OpenAIWhisper
│   ├── tts/            # PiperTTS, ElevenLabs
│   └── llm/            # GeminiAdapter
├── audio/
│   ├── recorder.py     # Captura de mic con VAD
│   └── player.py       # Reproductor interrumpible
├── main.py
└── config.yaml         # Para hacer switch entre Local/Remote
```
