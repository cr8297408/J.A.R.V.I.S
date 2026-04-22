# Plan: Jarvis 100% Local con Gemma 4 — Cero APIs externas, acceso universal

> **Estado actual**: 4 proveedores externos pagos (Gemini API, Groq, OpenRouter, Anthropic/Claude)
> **Estado objetivo**: Ollama + Gemma 4 + Accessibility API + OpenCode — gratis, offline, sin API keys, para todos

---

## Los tres modos de Jarvis

Jarvis tiene tres modos de operación distintos. El IntentRouter decide en tiempo real cuál activar.

| Modo | Activación | Motor | Qué hace |
|---|---|---|---|
| **GENERAL** | Conversación, preguntas, dictado | `gemma4:general` vía Ollama | Responde preguntas, explica cosas, charla libre |
| **PC CONTROL** | Comandos de acción sobre el SO | `gemma4:pc` + Screen Reader Engine | Controla cualquier app, lee pantalla, navega UI |
| **CODING** | Comandos de programación | `gemma4:code` + OpenCode vía PTY | Agente de coding: crea archivos, commitea, refactoriza |

Cada modo tiene su propio pipeline. El router es la pieza que los conecta.

---

## Contexto del problema

Jarvis actualmente depende de:

| Archivo | Proveedor | Requiere | Costo |
|---|---|---|---|
| `adapters/llm/gemini_summarizer.py` | Google Gemini API | `GEMINI_API_KEY` | Pago |
| `adapters/llm/groq_summarizer.py` | Groq API | `GROQ_API_KEY` | Límites gratis |
| `adapters/llm/openrouter_summarizer.py` | OpenRouter | `OPENROUTER_API_KEY` | Límites gratis |
| `adapters/llm/claude_api_adapter.py` | Anthropic Claude | `ANTHROPIC_API_KEY` | Pago |

**Ningún usuario puede usar Jarvis sin al menos una API key.** Eso es una barrera de entrada que excluye exactamente a las personas que más lo necesitan.

---

## Inspiración: cómo funciona JAWS / NVDA

JAWS y NVDA son los lectores de pantalla más usados del mundo para personas con discapacidad visual. La clave de su poder está en **cómo** leen el PC — y eso define nuestra arquitectura.

**JAWS no tiene un "adapter de Excel" ni un "adapter de Word".** Lo que hace es:

```
Windows UI Automation API  (árbol de accesibilidad)
            ↓
  Lee nodos: botones, celdas, menús, diálogos, texto
  de CUALQUIER aplicación — sin importar cuál sea
            ↓
    Convierte ese árbol a voz (TTS)
```

La Accessibility API del sistema operativo expone **toda la UI** como un árbol de nodos con texto semántico. No importa si es Excel, Word, Chrome, Photoshop — todas las apps tienen ese árbol. JAWS lo lee. Jarvis también puede.

**Conclusión arquitectural**: en lugar de escribir adaptadores específicos por aplicación (frágiles, limitados, imposibles de mantener), vamos a leer la UI universal del sistema operativo — igual que hacen las herramientas de accesibilidad profesionales.

---

## Aclaración crítica: Fine-tuning vs Function Calling

### ¿Para qué sirve el fine-tuning?

Fine-tuning entrena al modelo en **conocimiento y estilo**:
- Responder siempre en el formato JSON exacto de Jarvis
- Entender español rioplatense y jerga técnica
- Tener la personalidad Jarvis baked-in (sin system prompt largo en cada llamada)
- Clasificar intenciones (EXPLICAR / EJECUTAR / ESTADO) con alta precisión

### ¿Para qué NO sirve el fine-tuning?

Fine-tuning **no le da al modelo nuevas capacidades de ejecución**. El modelo ya sabe que existe Excel. Lo que no puede hacer es tocarlo — eso requiere código Python corriendo en la máquina del usuario.

**Controlar el PC = function calling + Accessibility API + herramientas Python.**
No es conocimiento, es un "brazo" que interactúa con la UI del sistema.

### Cuándo sí vale la pena fine-tunear

Solo cuando tenés 500+ ejemplos reales de uso corregidos manualmente. Antes de eso, un system prompt bien diseñado con few-shot examples logra el 80% del resultado desde el día uno, sin GPU especial.

---

## Arquitectura: Dos instancias de Gemma 4 + Screen Reader Engine

### Los dos modelos

| Instancia | Rol | Latencia | Cuándo se activa |
|---|---|---|---|
| `gemma4:pc` | Cerebro de acciones — decide qué herramienta usar y con qué argumentos | < 500ms | "abrí Excel", "leé la celda A1", "cerrá la ventana" |
| `gemma4:general` | Conversación, razonamiento, explicaciones | 1–3s | Preguntas, dictado, charla libre, nada de acción en pantalla |

Ambos via Ollama en `localhost`. En hardware potente corren en paralelo; en hardware limitado se carga el que corresponda según contexto.

### Por qué Ollama

- **Cero setup para el usuario final** — `ollama pull gemma4` y listo
- **API compatible con OpenAI** — el cliente `AsyncOpenAI` existente funciona apuntando a `localhost:11434`
- **Function calling nativo** en Gemma 4 — necesario para el sistema de herramientas
- **Multimodal** — Gemma 4 puede ver screenshots (fallback universal para leer pantalla)
- **Cross-platform**: Mac (Apple Silicon con Metal), Windows (CUDA/CPU), Linux
- **100% offline** una vez descargado el modelo

---

## Diagrama de arquitectura completo

```
┌─────────────────────────────────────────────────────────────────────────┐
│                            JARVIS v2                                    │
│                                                                         │
│  Micrófono ──► Whisper (local) ──► Texto del usuario                    │
│                                           │                             │
│                                     IntentRouter                        │
│                                    /      |      \                      │
│                          ¿General? │  ¿PC?│  ¿Coding?                   │
│                               │         │         │                     │
│                        gemma4:general  gemma4:pc  gemma4:code            │
│                          (Ollama)     (Ollama)    (Ollama)               │
│                               │         │         │                     │
│                               │    ToolDispatch  PTY(opencode)          │
│                               │         │         │                     │
│                               │    ┌────┴────┐    │                     │
│                               │    │Screen   │   Filtro TUI             │
│                               │    │Reader   │   (limpia output)        │
│                               │    │Engine   │    │                     │
│                               │    └────┬────┘    │                     │
│                               │         │         │                     │
│                               │   Capa 1 │ Capa 2  │                    │
│                               │   UIA/   │ Vision  │                    │
│                               │   NSAcc  │ fallback│                    │
│                               │         │         │                     │
│                               └────┬────┴────┬────┘                     │
│                                    │         │                          │
│                             Confirmación  Respuesta                     │
│                               vocal         oral                        │
│                                    └────┬────┘                          │
│                          TTS (macOS say / edge-tts / Coqui)             │
│                                         │                               │
│                                    Altavoz ◄── Usuario escucha          │
└─────────────────────────────────────────────────────────────────────────┘
                           OFFLINE. GRATIS. PARA TODOS.
```

---

## Las tres capas del Screen Reader Engine

### Capa 1 — Accessibility API nativa (la correcta, la que usa JAWS)

Lee el árbol de UI del sistema operativo. Sin OCR, sin screenshots, sin fricciones. Acceso semántico real a lo que hay en pantalla.

| Plataforma | Librería | API del SO |
|---|---|---|
| Windows | `pywinauto` | UI Automation (UIA) / MSAA |
| Mac | `pyobjc` + `AppKit` | NSAccessibility |
| Linux | `pyatspi` | AT-SPI (para apps GTK/Qt) |

**Qué puede hacer con esta capa**:
- Leer el contenido de cualquier ventana activa, incluso sin que el usuario diga qué app tiene abierta
- Navegar menús, botones, celdas, listas — sin tocar el mouse
- Detectar cambios en la UI (notificaciones, alertas, errores) para hablarlos proactivamente
- Interactuar con controles de forma accesible (click, input, scroll)

**Ejemplo conceptual en Windows**:
```python
# Leer el contenido de la ventana activa (cualquier app)
desktop = Desktop(backend="uia")
ventana_activa = desktop.window(active_only=True)
texto = ventana_activa.wrapper_object().texts()
# → Jarvis habla lo que hay ahí
```

**Ejemplo conceptual en Mac**:
```python
# Via pyobjc + NSAccessibility
import AppKit
app = AppKit.NSWorkspace.sharedWorkspace().frontmostApplication()
# → navegar el árbol de accesibilidad del proceso activo
```

### Capa 2 — Gemma 4 Vision (fallback universal)

Gemma 4 es multimodal — puede ver imágenes. Para apps que no implementan bien la Accessibility API (apps legacy, juegos, apps Electron mal armadas):

```
Screenshot() → Gemma 4 Vision → "Señor, hay un formulario con tres campos:
                                  nombre, email y teléfono. El campo activo es nombre."
```

**Uso típico**:
- El usuario dice "¿qué hay en pantalla?" → screenshot → Gemma 4 lo describe oralmente
- La app activa no tiene Accessibility API implementada → fallback a vision
- Verificación visual después de ejecutar una acción ("¿quedó bien?")

### Capa 3 — pyautogui (ejecución de acciones)

Mouse y teclado virtuales. Funciona en cualquier plataforma cuando las capas superiores no pueden ejecutar una acción específica.

```python
# Escribir texto donde está el cursor
pyautogui.typewrite("hola mundo", interval=0.05)

# Click en coordenadas (último recurso)
pyautogui.click(x=450, y=320)
```

---

## Módulo: Screen Reader Engine

**Archivo nuevo**: `core/screen_reader/engine.py`

Este módulo es el corazón de la capacidad de accesibilidad. Es el equivalente al motor de JAWS/NVDA, pero construido sobre Jarvis.

### Interfaz pública del engine

```python
class ScreenReaderEngine:
    async def read_active_window(self) -> str
    """Lee y devuelve el contenido textual de la ventana activa."""

    async def read_focused_element(self) -> str
    """Lee el elemento de UI que tiene el foco (celda actual, campo activo, etc.)"""

    async def describe_screen(self) -> str
    """Descripción completa de la pantalla — usa Vision si Accessibility falla."""

    async def navigate(self, direction: str) -> str
    """Navega: 'arriba', 'abajo', 'siguiente_campo', 'anterior', 'tab'"""

    async def announce_changes(self, callback) -> None
    """Monitorea cambios en la UI y llama callback cuando algo nuevo aparece."""

    async def click_element(self, description: str) -> bool
    """Hace click en un elemento descripto en lenguaje natural: 'el botón Guardar'"""

    async def type_text(self, text: str) -> None
    """Escribe texto en el elemento activo."""

    async def get_ui_tree(self) -> dict
    """Devuelve el árbol completo de la UI activa (para que Gemma razone sobre él)."""
```

### Resolución de plataforma en runtime

```python
import platform

def create_screen_reader() -> ScreenReaderEngine:
    os_name = platform.system()
    if os_name == "Windows":
        from core.screen_reader.backends.windows import WindowsBackend
        return ScreenReaderEngine(backend=WindowsBackend())
    elif os_name == "Darwin":
        from core.screen_reader.backends.macos import MacOSBackend
        return ScreenReaderEngine(backend=MacOSBackend())
    else:
        from core.screen_reader.backends.linux import LinuxBackend
        return ScreenReaderEngine(backend=LinuxBackend())
```

---

## Módulo: Tool Dispatch (function calling)

**Archivo nuevo**: `core/tool_dispatch/dispatcher.py`

Gemma 4 decide qué herramienta usar; el dispatcher la ejecuta. No hay lógica de decisión acá — solo ejecución.

### Herramientas registradas

```python
TOOLS = [
    # Lectura de pantalla
    {
        "name": "read_screen",
        "description": "Lee en voz alta el contenido de la ventana activa o elemento enfocado",
        "parameters": {
            "target": "active_window | focused_element | full_screen"
        }
    },
    # Navegación
    {
        "name": "navigate_ui",
        "description": "Navega por la interfaz: siguiente campo, anterior, arriba, abajo",
        "parameters": {
            "direction": "next | prev | up | down | tab | shift_tab"
        }
    },
    # Escritura
    {
        "name": "type_text",
        "description": "Escribe texto en el elemento activo",
        "parameters": {
            "text": "string"
        }
    },
    # Apps
    {
        "name": "open_app",
        "description": "Abre una aplicación por nombre",
        "parameters": {
            "name": "string"  # "Excel", "Word", "Chrome", "Notepad"
        }
    },
    {
        "name": "close_app",
        "description": "Cierra la ventana activa o una app por nombre",
        "parameters": {
            "name": "string | null"
        }
    },
    {
        "name": "switch_window",
        "description": "Cambia a otra ventana o app abierta",
        "parameters": {
            "name": "string"
        }
    },
    # Acciones universales
    {
        "name": "press_shortcut",
        "description": "Ejecuta un atajo de teclado",
        "parameters": {
            "keys": "string"  # "ctrl+s", "alt+f4", "ctrl+z"
        }
    },
    {
        "name": "click_element",
        "description": "Hace click en un elemento descripto en lenguaje natural",
        "parameters": {
            "description": "string"  # "el botón Guardar", "el menú Archivo"
        }
    },
    {
        "name": "describe_screen",
        "description": "Describe visualmente lo que hay en pantalla (usa Gemma Vision)",
        "parameters": {}
    },
    # Portapapeles
    {
        "name": "copy_selection",
        "description": "Copia el texto seleccionado al portapapeles",
        "parameters": {}
    },
    {
        "name": "paste_text",
        "description": "Pega el contenido del portapapeles",
        "parameters": {}
    },
    # Sistema
    {
        "name": "run_command",
        "description": "Ejecuta un comando de terminal (requiere confirmación vocal)",
        "parameters": {
            "command": "string"
        }
    }
]
```

**Clave**: estas herramientas son suficientes para controlar CUALQUIER aplicación. No hay "ExcelTool", no hay "WordTool" — la Accessibility API del SO se encarga de la abstracción.

---

## Módulo: Modo Coding — OpenCode + PTY

### ¿Qué es OpenCode?

OpenCode es un agente de coding TUI open-source (escrito en Go), equivalente a Claude Code pero sin dependencia de Anthropic. Soporta cualquier backend LLM compatible con OpenAI — incluyendo Ollama. Reemplaza directamente la sesión `ClaudeCodePtySession` existente.

**Repo**: `https://github.com/sst/opencode`  
**Instalación**: `brew install sst/tap/opencode` (Mac) / binario para Windows/Linux

### Por qué OpenCode en lugar de aider, continue.dev, etc.

| Herramienta | TUI | Soporte Ollama | Modelo de agente | PTY-friendly |
|---|---|---|---|---|
| OpenCode | Sí (Go TUI) | Sí nativo | Agente con tools | Sí |
| Aider | Sí (Python) | Sí | Agente con tools | Sí |
| Continue.dev | No (VSCode ext) | Sí | No es agente | No |
| Claude Code | Sí (React/Ink) | No | Agente con tools | Sí (ya implementado) |

OpenCode tiene el TUI más limpio para parsear por PTY y soporte nativo de Ollama sin hacks.

### Configuración de OpenCode para usar Ollama

OpenCode se configura via `~/.config/opencode/config.json`:

```json
{
  "providers": {
    "ollama": {
      "models": ["gemma4:latest", "qwen2.5-coder:latest"]
    }
  },
  "model": "ollama/gemma4:latest"
}
```

### Modelo recomendado para coding

Para el modo coding, Gemma 4 general funciona, pero existe un modelo más especializado en código:

| Modelo | Fuerte en | Tamaño |
|---|---|---|
| `gemma4:latest` | General + código | 12B / 27B |
| `qwen2.5-coder:latest` | Código puro, muy preciso | 7B / 14B |
| `deepseek-coder-v2:latest` | Código + razonamiento | 16B |

**Recomendación**: empezar con `qwen2.5-coder:7b` para hardware limitado o `gemma4:12b` si el hardware lo permite. Configurable vía `JARVIS_CODE_MODEL`.

### OpenCodePtySession — migración desde ClaudeCodePtySession

Ya existe `core/session/claude_code_pty_session.py` con toda la infraestructura PTY. La migración es casi directa:

**Archivo nuevo**: `core/session/opencode_pty_session.py`

Diferencias respecto a `ClaudeCodePtySession`:
1. El comando PTY cambia de `["claude"]` a `["opencode"]`
2. La `TUI_BLACKLIST` se actualiza con los artefactos del TUI de OpenCode (spinners, headers, etc.)
3. El modelo se configura vía variable de entorno en lugar de hardcodeado

```python
# Lo que cambia en el constructor
wrapper = PtyCLIWrapper(["opencode"])  # era ["claude"]

# La TUI_BLACKLIST se ajusta al output de OpenCode
TUI_BLACKLIST_OPENCODE = [
    "opencode",           # header
    "model:",             # info del modelo en status bar
    "tokens:",            # contador de tokens
    "Running",            # tool execution status
    # ... (se completa al probar el TUI real)
]
```

El resto del patrón es idéntico: VAD → GhostTyper → PTY → Filtro TUI → cola → Gemma 4 summarizer → TTS.

### Flujo del modo Coding

```
Usuario dice: "creá un archivo utils.py con una función que calcule el factorial"
                      ↓
              IntentRouter → CODING
                      ↓
              OpenCodePtySession activa
                      ↓
              GhostTyper inyecta el comando en el PTY de OpenCode
                      ↓
              OpenCode (con gemma4:code vía Ollama) ejecuta:
              - crea utils.py
              - escribe la función
              - responde en el TUI
                      ↓
              Filtro TUI limpia el output (igual que con Claude Code)
                      ↓
              gemma4:general summariza el output para TTS
                      ↓
              TTS: "Señor, el archivo utils.py fue creado con la función factorial."
```

---

## Módulo: Intent Router

**Archivo nuevo**: `core/intent_router.py`

Clasifica cada comando de voz en uno de los tres modos. Tres etapas en cascada:

### Etapa 1 — Keywords de coding (0ms, sin LLM, primera prioridad)

```python
CODING_KEYWORDS = {
    # Archivos de código
    "creá un archivo", "crear archivo", "nuevo archivo",
    "editá el archivo", "modificá", "refactorizá",
    # Git
    "commitear", "commit", "pusheá", "push", "pull", "branch",
    "mergeá", "merge", "stash",
    # Código
    "escribí una función", "escribí una clase", "escribí un test",
    "arreglá el bug", "fix", "corregí el error",
    "instalá el paquete", "npm install", "pip install",
    "corré los tests", "ejecutá los tests",
    # Proyecto
    "modo código", "modo coding", "modo programación",
    "opencode", "activá opencode",
}
```

Si hay match → modo **CODING** → `OpenCodePtySession`

### Etapa 2 — Keywords de PC Control (0ms, sin LLM)

```python
PC_ACTION_KEYWORDS = {
    # Apertura y cierre de apps
    "abrí", "abrir", "cerrá", "cerrar", "iniciá",
    # Lectura de pantalla
    "leé", "leer", "decime qué hay", "describí la pantalla",
    "qué dice", "qué hay en pantalla", "leeme esto",
    # Navegación UI
    "pasame a", "cambiá a", "siguiente campo", "anterior",
    "hacé tab", "scrolleá",
    # Escritura en UI
    "escribí en", "tipear", "dictá en el campo",
    # Acciones de UI
    "hacé click", "click en", "presioná", "guardá", "guardar",
    "copiá", "pegá", "seleccioná todo",
    # Apps de oficina (sin contexto de código)
    "excel", "word", "outlook", "explorador de archivos",
    # Modo explícito
    "modo pc", "modo accesibilidad", "leer pantalla",
}
```

Si hay match → modo **PC CONTROL** → `gemma4:pc` + `ScreenReaderEngine`

### Etapa 3 — Fallback: General (0ms)

Todo lo que no matchea las etapas 1 y 2 va a `gemma4:general`.

### Activación manual de modo

El usuario puede cambiar de modo explícitamente:
- "modo código" / "modo coding" → activa y mantiene modo CODING hasta "salir de modo código"
- "modo pc" → activa y mantiene modo PC CONTROL
- "modo general" / "salir del modo" → vuelve a routing automático

```python
class ModeState:
    ROUTING  = "routing"   # IntentRouter decide en cada comando
    CODING   = "coding"    # Siempre va a OpenCode
    PC       = "pc"        # Siempre va a ScreenReaderEngine
    GENERAL  = "general"   # Siempre va a gemma4:general
```

---

## Fases de implementación

### Estado del código existente relevante

Antes de implementar, hay que conocer lo que ya existe y se puede reutilizar:

| Archivo existente | Estado | En el plan nuevo |
|---|---|---|
| `core/cli/pty_wrapper.py` | Funciona — wrapper PTY genérico | Se reutiliza sin cambios |
| `core/session/claude_code_pty_session.py` | Funciona con Claude Code | Se migra a `opencode_pty_session.py` |
| `core/audio/vad_listener.py` | Funciona — VAD para voz | Se reutiliza sin cambios |
| `adapters/stt/ghost_typer.py` | Funciona — inyecta texto al PTY | Se reutiliza sin cambios |
| `adapters/tts/mac_say_tts.py` | Funciona — TTS en Mac | Se mantiene |
| `adapters/tts/edge_tts_adapter.py` | Funciona — TTS cross-platform | Se mantiene |
| `core/lexer/poc_lexer.py` | Funciona — streaming text parser | Se reutiliza |
| `adapters/llm/gemini_summarizer.py` | **Eliminar** | Reemplazado por OllamaAdapter |
| `adapters/llm/groq_summarizer.py` | **Eliminar** | Reemplazado por OllamaAdapter |
| `adapters/llm/openrouter_summarizer.py` | **Eliminar** | Reemplazado por OllamaAdapter |
| `adapters/llm/claude_api_adapter.py` | **Eliminar** | Reemplazado por OllamaAdapter |

---

### Fase 0 — Verificación de Gemma 4 en Ollama

Antes de escribir código, confirmar que Gemma 4 vía Ollama soporta:

- [ ] JSON mode / structured output — necesario para el schema actual de respuestas
- [ ] Function calling / tool use — necesario para el tool dispatch
- [ ] Streaming — necesario para baja latencia en TTS
- [ ] Multimodal (vision) — necesario para la Capa 2 del screen reader
- [ ] Context window ≥ 8k tokens — necesario para historial de conversación

**Hardware mínimo documentado**:

| Dispositivo | Modelo recomendado | RAM requerida | Latencia esperada |
|---|---|---|---|
| Mac M1/M2/M3 (8GB) | `gemma4:2b` | 8GB | ~300ms |
| Mac M1/M2/M3/M4 (16GB+) | `gemma4:12b` | 16GB | ~500ms |
| PC RTX 3060+ (12GB VRAM) | `gemma4:12b` | 12GB VRAM | ~200ms |
| PC RTX 4090 (24GB VRAM) | `gemma4:27b` | 24GB VRAM | ~150ms |
| PC sin GPU (CPU only) | `gemma4:2b` | 8GB RAM | 2–5s |

> **Nota crítica para discapacidad visual**: latencia > 2s empieza a ser frustrante y rompe el flujo de trabajo. En hardware sin GPU, usar el modelo 2B con system prompt ultra-optimizado.

---

### Fase 1 — OllamaAdapter (reemplaza los 4 adaptadores externos)

**Archivo nuevo**: `adapters/llm/ollama_adapter.py`

Implementa la misma interfaz que los adaptadores actuales para que la migración sea drop-in:

- `summarize(raw_text, user_command)` → `dict`
- `evaluate_response(user_input, context)` → `dict`
- `summarize_permission(details)` → `str`
- `stream_response(user_message)` → `AsyncGenerator`
- `vision_describe(screenshot_bytes)` → `str` ← **nuevo**, usa Gemma 4 multimodal

```python
# El cliente OpenAI apunta a Ollama local — cero cambio en la lógica
client = AsyncOpenAI(
    base_url=os.getenv("OLLAMA_HOST", "http://localhost:11434") + "/v1",
    api_key="ollama",  # Ollama no necesita API key real
)
```

Dos instancias:
```python
brain_pc      = OllamaAdapter(model=os.getenv("JARVIS_PC_MODEL",      "gemma4:latest"))
brain_general = OllamaAdapter(model=os.getenv("JARVIS_GENERAL_MODEL", "gemma4:latest"))
```

---

### Fase 2 — Screen Reader Engine

**Directorio nuevo**: `core/screen_reader/`

```
core/screen_reader/
├── engine.py           ← interfaz pública (ScreenReaderEngine)
├── backends/
│   ├── base.py         ← protocolo/ABC que todos los backends implementan
│   ├── windows.py      ← pywinauto + UI Automation
│   ├── macos.py        ← pyobjc + NSAccessibility
│   └── linux.py        ← pyatspi
└── vision_fallback.py  ← screenshot + Gemma 4 Vision cuando backend falla
```

**Dependencias nuevas por plataforma**:

| Plataforma | Dependencia | Instalación |
|---|---|---|
| Windows | `pywinauto` | `pip install pywinauto` |
| Mac | `pyobjc-framework-Cocoa` | `pip install pyobjc-framework-Cocoa` |
| Linux | `pyatspi` | `pip install pyatspi` |
| Todas | `Pillow` (screenshots) | `pip install Pillow` |
| Todas | `pyautogui` (ejecución) | `pip install pyautogui` |

---

### Fase 3 — Tool Dispatch

**Directorio nuevo**: `core/tool_dispatch/`

```
core/tool_dispatch/
├── dispatcher.py       ← recibe tool_call de Gemma, ejecuta la acción
├── registry.py         ← definición de todas las herramientas (TOOLS list)
└── confirmations.py    ← acciones peligrosas que requieren confirmación vocal
```

**Flujo de ejecución**:
```
Gemma 4 → tool_call: {"name": "type_text", "args": {"text": "hola mundo"}}
               ↓
         dispatcher.execute("type_text", {"text": "hola mundo"})
               ↓
         screen_reader.type_text("hola mundo")
               ↓
         resultado → TTS: "Señor, texto escrito."
```

**Acciones que requieren confirmación vocal**:
- `run_command` — ejecutar comandos de terminal
- `close_app` — cerrar una aplicación
- `press_shortcut` con atajos destructivos (`alt+f4`, `ctrl+w`, `ctrl+z` masivo)

---

### Fase 4 — Modo Coding: OpenCodePtySession

**Archivo nuevo**: `core/session/opencode_pty_session.py`

Migración casi directa desde `claude_code_pty_session.py`:
- Cambiar `["claude"]` → `["opencode"]` en `PtyCLIWrapper`
- Ajustar `TUI_BLACKLIST` con los artefactos del TUI de OpenCode (requiere testing manual del output)
- El modelo de código se configura en `~/.config/opencode/config.json` apuntando a Ollama

El `PtyCLIWrapper`, `GhostTyper`, `StreamingLexer` y TTS se reutilizan sin cambios.

---

### Fase 5 — Intent Router + ModeState

**Archivo nuevo**: `core/intent_router.py`

Tres etapas en cascada: keywords de coding → keywords de PC → fallback general.
Incluye `ModeState` para activación manual de modo por voz.

---

### Fase 6 — Migración del daemon y eliminación de dependencias externas

**Cambios en `core/server/jarvis_daemon.py` y `main.py`**:
- Reemplazar instanciación de `GeminiSummarizer` / `GroqSummarizer` / etc. por `OllamaAdapter`
- Inyectar `ScreenReaderEngine` en el loop principal
- Inyectar `ToolDispatcher`
- Inyectar `IntentRouter` + `ModeState`
- Integrar `OpenCodePtySession` como sesión del modo coding

**Archivos a eliminar**:
- `adapters/llm/gemini_summarizer.py`
- `adapters/llm/groq_summarizer.py`
- `adapters/llm/openrouter_summarizer.py`
- `adapters/llm/claude_api_adapter.py`

**`requirements.txt` después**:
```
# Core
click>=8.1
python-dotenv
pyaudio
webrtcvad
numpy
fastapi
uvicorn

# STT / TTS
openwakeword
mlx-whisper
edge-tts>=7.2.7

# LLM local (cliente HTTP compatible con Ollama — NO llama a la API de OpenAI)
openai>=1.0.0

# Screen Reader & PC Control
pyautogui
Pillow

# Plataforma — instalar solo lo que corresponde al SO
# Windows: pywinauto
# Mac:     pyobjc-framework-Cocoa
# Linux:   pyatspi

# OpenCode se instala como binario externo, no como dep de Python
# Ver: https://github.com/sst/opencode
```

**Variables de entorno eliminadas**:
- `GEMINI_API_KEY`
- `GROQ_API_KEY`
- `OPENROUTER_API_KEY`
- `ANTHROPIC_API_KEY`
- `STRIPE_KEY`

**Variables nuevas**:
```
OLLAMA_HOST=http://localhost:11434        # default, configurable para red local
JARVIS_GENERAL_MODEL=gemma4:latest       # modo conversación
JARVIS_PC_MODEL=gemma4:latest            # modo control de PC
JARVIS_CODE_MODEL=qwen2.5-coder:latest   # modo coding (o gemma4 si se prefiere un solo modelo)
```

---

### Fase 7 — Script de instalación para el usuario final

El usuario nuevo ejecuta esto una sola vez:

```bash
# 1. Instalar Ollama
curl -fsSL https://ollama.ai/install.sh | sh   # Mac/Linux
# Windows: descargar instalador en ollama.com

# 2. Descargar los modelos (una sola vez)
ollama pull gemma4              # modelo general + PC control (~8-16GB)
ollama pull qwen2.5-coder:7b   # modelo de código (~4GB, opcional)

# 3. Instalar OpenCode (para modo coding)
brew install sst/tap/opencode   # Mac
# Windows/Linux: binario en github.com/sst/opencode/releases

# 4. Configurar OpenCode para usar Ollama
mkdir -p ~/.config/opencode
cat > ~/.config/opencode/config.json << 'EOF'
{
  "providers": { "ollama": { "models": ["qwen2.5-coder:7b", "gemma4:latest"] } },
  "model": "ollama/qwen2.5-coder:7b"
}
EOF

# 5. Instalar Jarvis
pip install jarvis-voice

# 6. Iniciar Jarvis
jarvis start
```

**Sin API keys. Sin cuentas. Sin pago. Sin internet después del paso 2.**

---

### Fase 7 (Opcional) — Fine-tuning de Gemma 4

**Solo cuando haya 500+ ejemplos reales de uso corregidos.**

#### Qué entrenar

1. **Formato JSON estricto**: que responda siempre en el schema exacto de Jarvis sin desviarse
2. **Clasificación de intenciones** (EXPLICAR/EJECUTAR/ESTADO/RESPUESTA) en español rioplatense
3. **Personalidad Jarvis**: "Señor", conciso, sin markdown, sin leer código
4. **Mapeo de comandos de voz a tool calls**: "abrí el Chrome" → `{"name": "open_app", "args": {"name": "Chrome"}}`

#### Herramienta: Unsloth + QLoRA

```bash
pip install unsloth
```

Permite fine-tunear Gemma 4 12B en una RTX 4090 (24GB VRAM). Sin Unsloth necesitarías una A100.

#### Flujo

1. Usar Jarvis 2–4 semanas con logs activados
2. Revisar y corregir los ejemplos manualmente (el paso más importante)
3. Fine-tunear con Unsloth
4. Exportar a formato GGUF
5. Cargar en Ollama: `ollama create gemma4-jarvis -f Modelfile`
6. Cambiar `JARVIS_PC_MODEL=gemma4-jarvis`

---

## Orden de ejecución recomendado

| # | Fase | Tarea | Complejidad | Impacto | Desbloquea |
|---|---|---|---|---|---|
| 1 | F1 | `OllamaAdapter` — reemplaza los 4 adaptadores externos | Baja | Alto | Todo lo demás |
| 2 | F6 | Migrar daemon + eliminar deps externas | Baja | Alto | Jarvis funciona 100% local |
| 3 | F4 | `OpenCodePtySession` — modo coding con OpenCode | Baja | Muy alto | Coding por voz sin API keys |
| 4 | F5 | `IntentRouter` + `ModeState` — tres modos | Baja | Alto | Routing automático |
| 5 | F2 | `ScreenReaderEngine` — backend Windows (pywinauto) | Media | Muy alto | Control universal de PC en Win |
| 6 | F3 | `ToolDispatcher` + registry de herramientas | Media | Muy alto | Ejecución de comandos de voz |
| 7 | F2 | Backend Mac (NSAccessibility) | Media | Alto | Control de PC en Mac |
| 8 | F2 | Vision fallback (Gemma 4 + screenshot) | Baja | Alto | Cobertura total de apps |
| 9 | F7 | Script de instalación + docs para usuario final | Baja | Muy alto | Usuarios sin conocimiento técnico |
| 10 | F8 | Fine-tuning con Unsloth | Muy alta | Medio | Precisión + velocidad mejoradas |

---

## Lo que esto habilita

- **Acceso universal**: cualquier persona puede usar Jarvis — sin cuentas, sin pago, sin API keys
- **Privacidad total**: ningún comando de voz, ninguna línea de código sale de la máquina jamás
- **Funcionamiento offline**: sin internet, sin dependencia de terceros, sin riesgo de que una API suba precios o se caiga
- **Tres modos, una voz**: conversación libre, control de cualquier app de PC, y agente de coding — todo activado por voz sin tocar el teclado
- **Control universal del PC**: cualquier aplicación — Excel, Word, Chrome, Photoshop, lo que sea — sin mouse ni teclado, igual que JAWS pero con comprensión de lenguaje natural
- **Coding 100% local**: OpenCode + qwen2.5-coder via Ollama — mismo nivel que Claude Code pero sin pagar nada
- **Paridad con JAWS/NVDA**: mismas APIs de accesibilidad, mismo nivel de control, pero además el modelo *entiende* lo que está leyendo y puede actuar sobre ello
- **Escalable a cualquier hardware**: desde una PC sin GPU (modelo 2B) hasta una estación con 4090 (modelo 27B)
