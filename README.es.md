<div align="right">

[![🇺🇸 English](https://img.shields.io/badge/🇺🇸-English-blue?style=for-the-badge)](./README.md)
[![🇪🇸 Español](https://img.shields.io/badge/🇪🇸-Español-red?style=for-the-badge)](./README.es.md)

</div>

# J.A.R.V.I.S. — Extensión de Voz para Gemini CLI

> *Just A Rather Very Intelligent System*

**J.A.R.V.I.S.** es una capa inteligente y de voz sobre el [Gemini CLI](https://github.com/google-gemini/gemini-cli). Intercepta la salida de texto de Gemini, la resume de forma inteligente (especialmente los bloques de código) y te permite interactuar con tu co-piloto de IA completamente **manos libres** mediante comandos de voz.

En lugar de leer paredes de código en voz alta, J.A.R.V.I.S. dice cosas como:
> *"He generado el script de Python usando pandas tal como pediste. ¿Lo ejecuto o lo guardo en un archivo?"*

---

## ✨ Características

| Característica | Descripción |
|---|---|
| 🧠 **Resumen Inteligente** | Los bloques de código nunca se leen textualmente. Pasan por un filtro de resumen con Gemini Flash antes de llegar a tus oídos. |
| 🎙️ **Motor STT Híbrido** | Cambia entre STT local (MLX Whisper en Apple Silicon) y remoto (API de OpenAI Whisper). |
| 🔊 **Motor TTS Híbrido** | Elige entre `mac say` (latencia cero), ElevenLabs (calidad cinematográfica) o Edge TTS (nube, gratis). |
| ⚡ **Barge-In / Interrupción** | Interrumpe a J.A.R.V.I.S. en medio de una frase simplemente hablando. Un módulo VAD (Detección de Actividad de Voz) escucha constantemente y detiene el TTS al instante. |
| 🎛️ **PTY Wrapper** | Un envoltor de pseudo-terminal transparente que se sitúa entre tú y la TUI de Gemini sin modificar su renderizado visual. |
| 🔗 **Hooks de Gemini CLI** | Un hook `after_model` intercepta las respuestas del LLM mediante un socket TCP local para arquitecturas basadas en daemon. |
| 🌐 **Backends LLM Modulares** | Cambia el cerebro de resumen entre Gemini, Groq (Llama 3) u OpenRouter sin tocar la lógica central. |

---

## 🏗️ Arquitectura

```
┌─────────────────────────────────────────────────────────┐
│                    Usuario (Tú)                         │
│          Entrada de Voz           Entrada de Teclado    │
└──────────────┬──────────────────────────┬──────────────┘
               │                          │
       ┌───────▼────────┐        ┌────────▼────────┐
       │  VAD Listener  │        │   PTY Wrapper   │
       │  (Barge-in)    │        │  (gemini CLI)   │
       └───────┬────────┘        └────────┬────────┘
               │                          │
               │        Salida cruda TUI  │
               │        ┌─────────────────┘
               │        ▼
               │  ┌─────────────────┐
               │  │  Limpiador TUI  │  Elimina códigos ANSI,
               │  │  / Line Filter  │  caracteres de caja,
               │  └────────┬────────┘  ruido de la UI
               │           │
               │           ▼
               │  ┌─────────────────┐
               │  │ Streaming Lexer │  Detecta TEXTO vs BLOQUE_CÓDIGO
               │  └────────┬────────┘
               │           │
               │    ┌──────┴───────┐
               │    │              │
               │  TEXTO         CÓDIGO
               │    │              │
               │    │       ┌──────▼──────────┐
               │    │       │ Resumidor LLM   │  Gemini / Groq /
               │    │       │                 │  OpenRouter
               │    │       └──────┬──────────┘
               │    │              │
               └────┼──────────────┤  interrupt_event
                    ▼              ▼
               ┌─────────────────────┐
               │     Motor TTS       │  mac_say / ElevenLabs /
               │                     │  Edge TTS
               └─────────────────────┘
```

### Mapa de Módulos

```
gemini-extension-spech/
├── main.py                     # Orquestador: bucle PTY + multiplexación I/O
├── core/
│   ├── audio/
│   │   └── vad_listener.py     # WebRTC VAD + hilo de micrófono (barge-in)
│   ├── lexer/
│   │   └── poc_lexer.py        # Lexer streaming: detección TEXTO vs BLOQUE_CÓDIGO
│   ├── cli/
│   │   └── pty_wrapper.py      # Envoltor de pseudo-terminal para la TUI de Gemini
│   ├── integration/            # Utilidades de integración
│   └── server/                 # Servidor daemon TCP local
├── adapters/
│   ├── llm/
│   │   └── gemini_summarizer.py  # Adaptador LLM (Gemini / Groq / OpenRouter)
│   ├── tts/
│   │   ├── mac_say_tts.py        # Adaptador del comando nativo `say` de macOS
│   │   └── edge_tts_adapter.py   # Adaptador Microsoft Edge TTS
│   └── stt/
│       ├── mlx_stt.py            # Whisper local en Apple Silicon (MLX)
│       └── ghost_typer.py        # Escribe el texto transcrito en el PTY
├── hooks/
│   ├── after_model.py          # Hook de Gemini CLI: envía salida del LLM al daemon
│   └── notification.py         # Hook de notificación de Gemini CLI
├── apps/
│   └── jarvis-landing/         # App web landing page
├── install.sh                  # Instalador en un comando (macOS + Linux)
├── start.sh                    # Script de arranque (activa venv + ejecuta main.py)
├── requirements.txt
└── .env.example
```

---

## 🚀 Inicio Rápido

### Prerequisitos

- **Python 3.10+**
- **Node.js** (para el Gemini CLI)
- **macOS** (objetivo principal) o Linux Debian/Ubuntu
- Un **micrófono** conectado a tu máquina

### 1. Clona el Repositorio

```bash
git clone https://github.com/your-username/gemini-extension-spech.git
cd gemini-extension-spech
```

### 2. Ejecuta el Instalador

El instalador lo gestiona todo: dependencias del sistema (portaudio), Gemini CLI, entorno virtual de Python y el comando global `jarvis`.

```bash
chmod +x install.sh
./install.sh
```

### 3. Configura las API Keys

```bash
# El instalador crea .env automáticamente a partir de .env.example
# Ábrelo y rellena tus claves:
nano .env
```

Consulta [Configuración](#%EF%B8%8F-configuración) más abajo para todos los valores disponibles.

### 4. Lanza J.A.R.V.I.S.

```bash
# Desde cualquier carpeta de tu máquina (después de que install.sh cree el comando global):
jarvis

# O directamente desde la carpeta del proyecto:
./start.sh
```

---

## ⚙️ Configuración

Toda la configuración se gestiona mediante el archivo `.env`.

### API Keys

| Variable | Requerida | Descripción |
|---|---|---|
| `GEMINI_API_KEY` | ✅ | Clave de Google AI Studio — usada para el resumen. Consíguela en [aistudio.google.com](https://aistudio.google.com) |
| `GROQ_API_KEY` | Opcional | Clave de Groq Cloud — latencia ultra-baja con Llama 3. Consíguela en [console.groq.com](https://console.groq.com) |
| `OPENROUTER_API_KEY` | Opcional | Acceso a 20+ modelos gratuitos con una sola clave. Consíguela en [openrouter.ai](https://openrouter.ai) |
| `ELEVENLABS_API_KEY` | Opcional | Calidad de TTS cinematográfica. Consíguela en [elevenlabs.io](https://elevenlabs.io) |
| `ELEVENLABS_VOICE_ID` | Opcional | ID de voz dentro de ElevenLabs a utilizar |

### Selección de Motor

| Variable | Valores | Por defecto | Descripción |
|---|---|---|---|
| `ACTIVE_BRAIN_ENGINE` | `gemini`, `groq`, `openrouter` | `gemini` | Qué LLM usar para el filtro cognitivo/resumen |
| `ACTIVE_TTS_ENGINE` | `mac_say`, `elevenlabs`, `kokoro` | `mac_say` | Qué motor TTS usar para la salida de voz |

---

## 🔈 Motores TTS

| Motor | Latencia | Calidad | Costo | Plataforma |
|---|---|---|---|---|
| `mac_say` | ⚡ Cero | Buena | Gratis | Solo macOS |
| `edge_tts` | Rápida | Muy Buena | Gratis | Multiplataforma |
| `elevenlabs` | ~500ms | Cinematográfica | De pago (tier gratis) | Multiplataforma |

---

## 🧠 Backends LLM

| Motor | Velocidad | Notas |
|---|---|---|
| `gemini` | Rápido | Ventana de contexto de 1M tokens. Recomendado para resumen. |
| `groq` | ⚡ El más rápido | Ideal para voz en tiempo real. Usa Llama 3.3 / Mixtral. |
| `openrouter` | Variable | Acceso a 20+ modelos incluyendo gratuitos. |

---

## 🔗 Hooks de Gemini CLI (Arquitectura Alternativa)

Para una arquitectura **basada en daemon** donde el Gemini CLI corre de forma independiente y J.A.R.V.I.S. se conecta mediante el sistema oficial de hooks:

1. Configura el Gemini CLI para usar los hooks:
   ```bash
   # En tu GEMINI.md o config de gemini, apunta afterModelHook a:
   hooks/after_model.py
   ```

2. El hook lanza un servidor de socket TCP local en el puerto `49999` que recibe chunks de la respuesta del LLM y los envía al motor de voz.

---

## 🎙️ Barge-In: Cómo Funciona

J.A.R.V.I.S. usa **WebRTC VAD** (`webrtcvad`) en un hilo en segundo plano que monitorea constantemente tu micrófono.

1. J.A.R.V.I.S. empieza a hablar una respuesta.
2. Tú empiezas a hablar.
3. El VAD detecta actividad de voz en **~20ms**.
4. Un `threading.Event` compartido (`interrupt_event`) se activa.
5. El subproceso TTS se termina inmediatamente.
6. El sistema transiciona al estado `ESCUCHANDO`.

---

## 🛠️ Desarrollo

### Ejecutando Tests / POCs

```bash
# Probar sensibilidad de wake word / VAD
python test_oww_sensitivity.py

# Probar PTY + inyección en tmux
python test_tmux.py
python test_tmux_inject.py

# Probar ejecución directa de AppleScript
python test_applescript.py
```

### Logs de Depuración

J.A.R.V.I.S. escribe salida detallada de depuración en `debug_jarvis.log` en la raíz del proyecto. Cada ejecución limpia el log anterior. Contiene tanto los chunks PTY crudos como el texto limpiado enviado al cerebro.

```bash
tail -f debug_jarvis.log
```

---

## 📦 Dependencias

| Paquete | Propósito |
|---|---|
| `pyaudio` | Captura de micrófono |
| `webrtcvad` | Detección de Actividad de Voz (barge-in) |
| `numpy` | Procesamiento de buffer de audio |
| `google-generativeai` | API de Gemini para resumen |
| `groq` | Cliente de API de Groq |
| `openai` | API de Whisper de OpenAI (STT) |
| `edge-tts` | Adaptador Microsoft Edge TTS |
| `python-dotenv` | Carga del archivo `.env` |
| `fastapi` + `uvicorn` | Servidor HTTP/WS del daemon local |

---

## 🗺️ Hoja de Ruta

- [x] PTY wrapper con multiplexación I/O transparente
- [x] Streaming Lexer (detección TEXTO vs BLOQUE_CÓDIGO)
- [x] Adaptadores de resumen Gemini + Groq
- [x] TTS macOS `say` + Edge TTS
- [x] Barge-in con WebRTC VAD
- [x] Integración con hooks de Gemini CLI
- [ ] Detección de palabra de activación ("Hey JARVIS")
- [ ] TTS local con Kokoro / Piper
- [ ] Soporte completo en Linux para MLX STT (backend alternativo de Whisper)
- [ ] UI de configuración mediante la landing page

---

## 📄 Licencia

MIT License — consulta [LICENSE](./LICENSE) para más detalles.

---

<div align="center">
  <sub>Construido con ❤️ como parte del reto 100K · Impulsado por <a href="https://ai.google.dev/">Google Gemini</a></sub>
</div>
