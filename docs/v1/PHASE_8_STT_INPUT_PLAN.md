# Fase 8: Integración de Speech-to-Text (STT) - El Input de Voz

## Objetivo
Permitir que el usuario controle la Gemini CLI utilizando únicamente su voz. El flujo debe ser natural (manos libres), sin botones, y con feedback sonoro para indicar que el sistema está escuchando.

## Arquitectura del Flujo (Pipeline de Entrada)

El proceso de STT se dividirá en 4 etapas manejadas por el **Jarvis Daemon**:

### 1. El Despertar (Wake Word)
- **Tecnología:** `openWakeWord` (modelo `hey_jarvis`).
- **Acción:** Cuando el usuario dice "Hey Jarvis":
  1. Se dispara el evento de `Barge-in` (detiene cualquier TTS actual).
  2. Se reproduce un sonido nativo de sistema (ej: `afplay /System/Library/Sounds/Ping.aiff` en macOS) para indicar "Estoy escuchando".
  3. El hilo del micrófono cambia de estado: de "buscar Wake Word" a "grabar comando".

### 2. Grabación Inteligente (VAD Dinámico)
- **Tecnología:** Grabación en memoria (buffer) combinada con `webrtcvad`.
- **Acción:** Se comienza a grabar el audio crudo del usuario.
- **Condición de corte:** El sistema usa VAD (Voice Activity Detection) para medir cuándo el usuario dejó de hablar. Si detecta ~1.5 segundos de silencio continuo, corta la grabación automáticamente.

### 3. Transcripción (STT Engine)
- **Tecnología a definir:** 
  - *Opción A:* Local usando `mlx-whisper` (aprovecha los Apple Silicon M-series).
  - *Opción B:* Nube usando API (OpenAI Whisper / Groq) para máxima velocidad.
- **Acción:** Toma el buffer de audio grabado y lo convierte a una cadena de texto (ej: *"Explicame cómo hacer un fetch en Python"*).

### 4. Inyección en la CLI (Ghost Typing)
- **Tecnología:** `pynput` (Python) o `osascript` (AppleScript nativo).
- **Acción:** Como la Gemini CLI está corriendo en una terminal normal esperando input de teclado, el demonio tomará el texto transcrito y emulará las pulsaciones de teclado en la ventana activa, finalizando con un `Enter` para enviar el prompt.

## Pasos de Implementación Requeridos

1. **Refactorizar el Hilo de Audio:**
   - El archivo `core/audio/vad_listener.py` se convertirá en una máquina de estados de dos fases: 
     `ESTADO_ESPERA` (openWakeWord) -> `ESTADO_ESCUCHA` (Grabación + webrtcvad) -> `ESTADO_PROCESANDO` -> (vuelve al inicio).
2. **Implementar el Adaptador STT:**
   - Crear la carpeta `adapters/stt/` y programar el motor elegido (Local o Nube).
3. **Implementar el Inyector de Teclado:**
   - Crear una clase que se encargue de tipear el string resultante en el OS de forma segura.
4. **Manejo de Feedback Sonoro:**
   - Agregar funciones sencillas para reproducir SFX (Sound Effects) nativos de Mac al despertar y al terminar de grabar, mejorando la UX radicalmente.

---
*Decisión Pendiente del Usuario:* Definir si el motor STT será local (`mlx`) o en la nube (API).

## Decisión Arquitectónica: STT Local (MLX Whisper)
El usuario ha decidido implementar el enfoque **100% Local** para la transcripción de voz utilizando `mlx-whisper`.
*   **Razonamiento:** Se prioriza la privacidad, el funcionamiento offline y la independencia de APIs de pago o externas. Al estar en un entorno macOS (Apple Silicon asumido), el framework MLX de Apple permite ejecutar modelos de Whisper utilizando la GPU integrada con una latencia extremadamente baja, compitiendo de cerca con las APIs basadas en la nube.
*   **Impacto Técnico:** Requerirá instalar las dependencias `mlx` y `mlx-whisper`. El sistema descargará automáticamente el modelo elegido (ej. `mlx-community/whisper-tiny`) en la primera ejecución, lo que consumirá espacio en disco local, pero garantizará autonomía total a futuro.

## Progreso de la Fase 8
- [x] **Wake Word:** Integrado `openWakeWord` (modelo `hey_jarvis.onnx`). Ajustada sensibilidad a `0.35` para mejor detección de acentos.
- [x] **VAD + Grabación:** Implementado con `webrtcvad`. Corta a los 1.5s de silencio absoluto.
- [x] **STT Local:** Integrado `mlx-whisper` (modelo `small-mlx`). Se añadió **Acoustic Prompt Engineering** (`initial_prompt`) inyectando jerga técnica ("PR", "issue", "commit") para evitar alucinaciones (ej: transcribir "PR" como "perro").
- [x] **Inyección (Ghost Typer):** Usando `osascript` (AppleScript) para tipear como usuario en la terminal.

## Siguiente Fase (Fase 9): Pulido y Empaquetado
El sistema base (End-to-End) está completo y funcional. Los próximos pasos deben enfocarse en estabilización, distribución y usabilidad general.
