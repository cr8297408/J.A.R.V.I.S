<div align="right">

[![🇺🇸 English](https://img.shields.io/badge/🇺🇸-English-blue?style=for-the-badge)](./README.md)
[![🇪🇸 Español](https://img.shields.io/badge/🇪🇸-Español-red?style=for-the-badge)](./README.es.md)

</div>

# J.A.R.V.I.S. — Gemini Voice CLI Extension

> *Just A Rather Very Intelligent System*

**J.A.R.V.I.S.** is a voice-first intelligent layer on top of the [Gemini CLI](https://github.com/google-gemini/gemini-cli). It intercepts the raw text output from Gemini, intelligently summarizes it (especially code blocks), and lets you interact with your AI co-pilot completely **hands-free** via voice commands.

Instead of reading walls of code aloud, J.A.R.V.I.S. says things like:
> *"I've generated the Python script using pandas as requested. Should I execute it or save it to a file?"*

---

## ✨ Features

| Feature | Description |
|---|---|
| 🧠 **Intelligent Summarization** | Code blocks are never read verbatim. They pass through a Gemini Flash summarization filter before reaching your ears. |
| 🎙️ **Hybrid STT Engine** | Switch between local (MLX Whisper on Apple Silicon) and remote (OpenAI Whisper API) speech-to-text. |
| 🔊 **Hybrid TTS Engine** | Choose between `mac say` (zero latency), ElevenLabs (cinematic quality), or Edge TTS (cloud, free). |
| ⚡ **Barge-In / Interruption** | Interrupt J.A.R.V.I.S. mid-sentence just by speaking. A VAD (Voice Activity Detection) module constantly listens and halts the TTS instantly. |
| 🎛️ **PTY Wrapper** | A transparent pseudo-terminal wrapper that sits between you and the Gemini TUI without modifying its visual rendering at all. |
| 🔗 **Gemini CLI Hooks** | An `after_model` hook intercepts LLM responses via a local TCP socket for daemon-based architectures. |
| 🌐 **Modular LLM Backends** | Swap out the summarization brain between Gemini, Groq (Llama 3), or OpenRouter without changing core logic. |

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────┐
│                     User (You)                          │
│          Voice Input                Keyboard Input      │
└──────────────┬──────────────────────────┬──────────────┘
               │                          │
       ┌───────▼────────┐        ┌────────▼────────┐
       │  VAD Listener  │        │   PTY Wrapper   │
       │  (Barge-in)    │        │  (gemini CLI)   │
       └───────┬────────┘        └────────┬────────┘
               │                          │
               │         Raw TUI output   │
               │        ┌─────────────────┘
               │        ▼
               │  ┌─────────────────┐
               │  │  TUI Cleaner /  │  Strips ANSI codes,
               │  │  Line Filter    │  box-drawing chars,
               │  └────────┬────────┘  UI noise
               │           │
               │           ▼
               │  ┌─────────────────┐
               │  │ Streaming Lexer │  Detects TEXT vs CODE_BLOCK
               │  └────────┬────────┘
               │           │
               │    ┌──────┴───────┐
               │    │              │
               │  TEXT           CODE
               │    │              │
               │    │       ┌──────▼──────────┐
               │    │       │ LLM Summarizer  │  Gemini / Groq /
               │    │       │                 │  OpenRouter
               │    │       └──────┬──────────┘
               │    │              │
               └────┼──────────────┤  interrupt_event
                    ▼              ▼
               ┌─────────────────────┐
               │     TTS Engine      │  mac_say / ElevenLabs /
               │                     │  Edge TTS
               └─────────────────────┘
```

### Module Map

```
gemini-extension-spech/
├── main.py                     # Orchestrator: PTY loop + I/O multiplexing
├── core/
│   ├── audio/
│   │   └── vad_listener.py     # WebRTC VAD + microphone thread (barge-in)
│   ├── lexer/
│   │   └── poc_lexer.py        # Streaming lexer: TEXT vs CODE_BLOCK detection
│   ├── cli/
│   │   └── pty_wrapper.py      # Pseudo-terminal wrapper for the Gemini TUI
│   ├── integration/            # Integration utilities
│   └── server/                 # Local TCP daemon server
├── adapters/
│   ├── llm/
│   │   └── gemini_summarizer.py  # LLM adapter (Gemini / Groq / OpenRouter)
│   ├── tts/
│   │   ├── mac_say_tts.py        # macOS native `say` command adapter
│   │   └── edge_tts_adapter.py   # Microsoft Edge TTS adapter
│   └── stt/
│       ├── mlx_stt.py            # Apple Silicon local Whisper (MLX)
│       └── ghost_typer.py        # Types transcribed speech into the PTY
├── hooks/
│   ├── after_model.py          # Gemini CLI hook: pipes LLM output to daemon
│   └── notification.py         # Gemini CLI notification hook
├── apps/
│   └── jarvis-landing/         # Landing page web app
├── install.sh                  # One-command installer (macOS + Linux)
├── start.sh                    # Launch script (activates venv + runs main.py)
├── requirements.txt
└── .env.example
```

---

## 🚀 Quick Start

### Prerequisites

- **Python 3.10+**
- **Node.js** (for the Gemini CLI)
- **macOS** (primary target) or Debian/Ubuntu Linux
- A **microphone** connected to your machine

### 1. Clone the Repository

```bash
git clone https://github.com/your-username/gemini-extension-spech.git
cd gemini-extension-spech
```

### 2. Run the Installer

The installer handles everything: system dependencies (portaudio), Gemini CLI, Python virtual environment, and the global `jarvis` command.

```bash
chmod +x install.sh
./install.sh
```

### 3. Configure API Keys

```bash
# The installer creates .env automatically from .env.example
# Open it and fill in your keys:
nano .env
```

See [Configuration](#%EF%B8%8F-configuration) below for all available keys.

### 4. Launch J.A.R.V.I.S.

```bash
# From anywhere on your machine (after install.sh creates the global command):
jarvis

# Or directly from the project folder:
./start.sh
```

---

## ⚙️ Configuration

All configuration is managed via the `.env` file.

### API Keys

| Variable | Required | Description |
|---|---|---|
| `GEMINI_API_KEY` | ✅ | Google AI Studio key — used for summarization. Get it at [aistudio.google.com](https://aistudio.google.com) |
| `GROQ_API_KEY` | Optional | Groq Cloud key — ultra-low latency via Llama 3. Get it at [console.groq.com](https://console.groq.com) |
| `OPENROUTER_API_KEY` | Optional | Access 20+ free models with one key. Get it at [openrouter.ai](https://openrouter.ai) |
| `ELEVENLABS_API_KEY` | Optional | Cinematic TTS quality. Get it at [elevenlabs.io](https://elevenlabs.io) |
| `ELEVENLABS_VOICE_ID` | Optional | Voice ID within ElevenLabs to use |

### Engine Selection

| Variable | Values | Default | Description |
|---|---|---|---|
| `ACTIVE_BRAIN_ENGINE` | `gemini`, `groq`, `openrouter` | `gemini` | Which LLM to use for the cognitive/summarization filter |
| `ACTIVE_TTS_ENGINE` | `mac_say`, `elevenlabs`, `kokoro` | `mac_say` | Which TTS engine to use for voice output |

---

## 🔈 TTS Engines

| Engine | Latency | Quality | Cost | Platform |
|---|---|---|---|---|
| `mac_say` | ⚡ Zero | Good | Free | macOS only |
| `edge_tts` | Fast | Very Good | Free | Cross-platform |
| `elevenlabs` | ~500ms | Cinematic | Paid (free tier) | Cross-platform |

---

## 🧠 LLM Backends

| Engine | Speed | Notes |
|---|---|---|
| `gemini` | Fast | 1M context window. Recommended for summarization. |
| `groq` | ⚡ Fastest | Best for real-time voice. Uses Llama 3.3 / Mixtral. |
| `openrouter` | Variable | Access to 20+ models including free ones. |

---

## 🔗 Gemini CLI Hooks (Alternative Architecture)

For a **daemon-based** architecture where the Gemini CLI runs standalone and J.A.R.V.I.S. taps into it using the official hooks system:

1. Configure the Gemini CLI to use the hooks:
   ```bash
   # In your GEMINI.md or gemini config, point afterModelHook to:
   hooks/after_model.py
   ```

2. The hook launches a local TCP socket server on port `49999` that receives LLM response chunks and pipes them to the voice engine.

---

## 🎙️ Barge-In: How It Works

J.A.R.V.I.S. uses **WebRTC VAD** (`webrtcvad`) on a background thread that continuously monitors your microphone.

1. J.A.R.V.I.S. starts speaking a response.
2. You start talking.
3. VAD detects voice activity within **~20ms**.
4. A shared `threading.Event` (`interrupt_event`) is set.
5. The TTS subprocess is killed immediately.
6. The system transitions to `LISTENING` state.

---

## 🛠️ Development

### Running Tests / POCs

```bash
# Test wake word / VAD sensitivity
python test_oww_sensitivity.py

# Test PTY + tmux injection
python test_tmux.py
python test_tmux_inject.py

# Test raw AppleScript execution
python test_applescript.py
```

### Debug Logs

J.A.R.V.I.S. writes detailed debug output to `debug_jarvis.log` in the project root. Each run clears the previous log. It contains both the raw PTY chunks and the cleaned text sent to the brain.

```bash
tail -f debug_jarvis.log
```

---

## 📦 Dependencies

| Package | Purpose |
|---|---|
| `pyaudio` | Microphone capture |
| `webrtcvad` | Voice Activity Detection (barge-in) |
| `numpy` | Audio buffer processing |
| `google-generativeai` | Gemini API for summarization |
| `groq` | Groq API client |
| `openai` | OpenAI Whisper API (STT) |
| `edge-tts` | Microsoft Edge TTS adapter |
| `python-dotenv` | `.env` file loading |
| `fastapi` + `uvicorn` | Local daemon HTTP/WS server |

---

## 🗺️ Roadmap

- [x] PTY wrapper with transparent I/O multiplexing
- [x] Streaming Lexer (TEXT vs CODE_BLOCK detection)
- [x] Gemini + Groq summarization adapters
- [x] macOS `say` TTS + Edge TTS adapters
- [x] WebRTC VAD barge-in
- [x] Gemini CLI hooks integration
- [ ] Wake-word detection ("Hey JARVIS")
- [ ] Local TTS with Kokoro / Piper
- [ ] Full Linux support for MLX STT (alternative Whisper backend)
- [ ] Configuration UI via the landing page

---

## 📄 License

MIT License — see [LICENSE](./LICENSE) for details.

---

<div align="center">
  <sub>Built with ❤️ as part of the 100K Challenge · Powered by <a href="https://ai.google.dev/">Google Gemini</a></sub>
</div>
