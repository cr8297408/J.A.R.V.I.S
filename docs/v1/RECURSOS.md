# 📊 Huella del Sistema y Recursos (J.A.R.V.I.S.)

J.A.R.V.I.S. ha sido diseñado para ser un demonio ligero que actúa como intermediario cognitivo, delegando el "trabajo pesado" (como la generación LLM y las decisiones lógicas) a APIs externas en la nube (Groq, Gemini), mientras ejecuta tareas de baja latencia (STT, TTS, Wake Word) directamente en tu máquina local.

A continuación, un desglose del impacto en almacenamiento y recursos de hardware.

## 💾 Huella de Almacenamiento (Disco)

El proyecto en sí (scripts y configuraciones) pesa apenas unos pocos Megabytes, pero las dependencias de Inteligencia Artificial y Audio ocupan la mayor parte del espacio.

| Componente | Tamaño Aproximado | Descripción |
| :--- | :--- | :--- |
| **Código Fuente** | `< 2 MB` | Scripts de Python, Bash y archivos de configuración. |
| **Entorno Virtual (`.venv`)** | `~1.3 GB` | Dependencias de Python (`mlx`, `torch` o similares instalados por `openwakeword`, `edge-tts`, `webrtcvad`, etc). |
| **Modelo Whisper STT (MLX)** | `~460 MB` | El modelo de transcripción `whisper-small-mlx` (descargado automáticamente en `~/.cache/huggingface/` la primera vez que hablas). |
| **Modelos Wake Word (ONNX)** | `~5 MB` | Modelo ligero de `openwakeword` para detectar "Hey Jarvis". |
| **Total en Disco** | **~1.7 GB - 1.8 GB** | Espacio total requerido en tu disco duro para una instalación completa. |

---

## ⚡ Consumo de Recursos (CPU / RAM)

El consumo de recursos varía drásticamente dependiendo del estado del demonio:

### 1. Estado de Reposo (Standby / Esperando "Hey Jarvis")
En este estado, el demonio está escuchando el micrófono en un bucle infinito, pero usando motores altamente optimizados (`webrtcvad` y `openwakeword`).

- **CPU:** `~1% - 3%` (Prácticamente inactivo. `openwakeword` está diseñado para correr en microcontroladores, por lo que su impacto en una Mac o PC moderna es casi nulo).
- **RAM:** `~150 MB - 250 MB` (Mantiene el entorno de Python, el modelo ONNX en memoria y el socket TCP abierto).

### 2. Estado Activo (Grabación y Transcripción STT)
Una vez que dices "Hey Jarvis" y comienzas a hablar, el sistema graba tu comando y luego invoca el motor STT local (`mlx-whisper`).

- **CPU / GPU (Apple Silicon):** Picos de `15% - 30%` durante **1 a 2 segundos**. Al usar MLX, aprovecha los Neural Engines/GPU de la Mac, evitando estrangular la CPU tradicional.
- **RAM / VRAM (Unificada):** Picos de `~500 MB - 800 MB` mientras el modelo Whisper procesa el audio. Una vez transcrito, la memoria se libera rápidamente o queda en caché pasiva.

### 3. Estado de Evaluación y Habla (Cerebro LLM + TTS)
Cuando el terminal devuelve información y J.A.R.V.I.S. está pensando si debe intervenir, o cuando está hablando en voz alta.

- **CPU:** `~5% - 10%`. Generar la voz neuronal con `edge-tts` requiere un pequeño esfuerzo de red y decodificación de MP3 (que maneja `afplay`). Las llamadas al LLM (Groq) no consumen CPU local, solo red.
- **RAM:** Se mantiene estable alrededor de `~200 MB`.

---

## 🌎 Dependencia de Red (Internet)

J.A.R.V.I.S. requiere conexión a internet constante y de baja latencia para funcionar fluidamente:
- **Groq API / Gemini API**: Para la evaluación de intenciones y resumido (Envia fragmentos de texto de kilobytes).
- **Edge TTS (Microsoft)**: Para la generación de voz realista. Descarga un archivo de audio MP3 muy pequeño (`~10 KB - 50 KB` dependiendo de la longitud de la oración) en tiempo real.

*(La transcripción de tu voz STT y la detección de "Hey Jarvis" ocurren **100% offline** por privacidad).*
