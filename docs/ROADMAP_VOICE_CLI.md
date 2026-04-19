# JARVIS — Voice-First Programming CLI: Complete Roadmap

## Vision

Transform Jarvis from a PTY wrapper around Gemini CLI into a **standalone voice-first CLI for programming** — powered by Claude API, with its own tool system, skill registry, and a latency-first architecture.

The user speaks. Jarvis acts. Latency is the enemy. Every millisecond matters.

---

## Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│                    JARVIS VOICE CODING CLI                       │
│                                                                  │
│  [Wake Word]                                                     │
│      ↓                                                           │
│  [VAD + MLX Whisper STT] ←── barge-in thread                   │
│      ↓                                                           │
│  [Intent Pre-classifier]  ←── local model, no API call          │
│      ↓                                                           │
│  ┌───┴──────────────────────────────────┐                        │
│  ↓                                      ↓                        │
│  [Local Executor]              [Claude API (streaming)]          │
│  (git, file ops, search,       (complex reasoning,               │
│   shell commands)               code gen, analysis)              │
│  ↓                                      ↓                        │
│  └───────────────────┬──────────────────┘                        │
│                      ↓                                           │
│             [Voice Summarizer]  ←── never reads raw code         │
│                      ↓                                           │
│             [Streaming TTS]     ←── first token → speaker        │
│                      ↓                                           │
│                  [User hears]                                    │
└──────────────────────────────────────────────────────────────────┘
```

---

## Milestones

| # | Name | Goal |
|---|------|------|
| M1 | Foundation | Jarvis como CLI standalone con Claude API |
| M2 | Tool System | Herramientas de coding adaptadas para voz |
| M3 | Voice UX | UX de voz específico para programar |
| M4 | Latency Zero | Optimizaciones de latencia agresivas |
| M5 | Intelligence | Conciencia de contexto de código |
| M6 | Advanced | Multi-agente, MCP, LSP |

---

## Issues

### EPIC 1 — Foundation: Standalone CLI

#### Issue 1: Refactor entry point as standalone `jarvis` CLI
**Labels**: `epic:foundation`, `priority:critical`

Jarvis debe ser instalable como comando global (`pip install -e .` o similar).

**Tasks:**
- [ ] Crear `pyproject.toml` con entry point `jarvis = main:cli`
- [ ] Refactorizar `main.py` para soportar subcomandos: `jarvis start`, `jarvis config`, `jarvis doctor`
- [ ] Agregar `--backend` flag: `claude` | `gemini` | `groq`
- [ ] Help text por voz ("jarvis help" habla los comandos disponibles)
- [ ] Validación de env vars al startup con mensajes de error claros

**Latency impact**: ninguno (infraestructura)

---

#### Issue 2: Claude API direct integration
**Labels**: `epic:foundation`, `priority:critical`

Reemplazar el PTY wrapper de Gemini CLI con llamadas directas a la Claude API con streaming. El PTY queda como fallback cuando el usuario quiere wrappear un CLI externo.

**Tasks:**
- [ ] Crear `adapters/llm/claude_api_adapter.py` — streaming con `anthropic` SDK
- [ ] Implementar streaming response handler (chunks → lexer existente)
- [ ] Adaptar `poc_lexer.py` para manejar response de API (no PTY output)
- [ ] Tool use loop: detectar tool calls en el stream, ejecutar, enviar result
- [ ] Mantener historial de conversación en memoria
- [ ] Configurar model: `claude-opus-4-6` para razonamiento, `claude-haiku-4-5` para clasificación rápida

**Latency impact**: ALTO — streaming desde primer token, TTS empieza antes de que termine la respuesta

---

#### Issue 3: Multi-backend CLI adapter (Claude + Gemini + PTY mode)
**Labels**: `epic:foundation`, `priority:high`

El sistema de adapters ya existe para TTS/STT/LLM. Extender para soportar tres modos de operación:

```
MODE=api       → llama directamente Claude/Gemini API (mínima latencia)
MODE=pty       → wrappea un CLI externo (Claude Code CLI, Gemini CLI)
MODE=hybrid    → API para reasoning, PTY para tool execution
```

**Tasks:**
- [ ] Crear `core/backend/` con `BackendBase`, `APIBackend`, `PTYBackend`
- [ ] Factory pattern seleccionable via `JARVIS_MODE` env var
- [ ] Unificar interfaz: ambos backends emiten eventos al mismo lexer/TTS pipeline
- [ ] Tests de smoke para cada modo

---

#### Issue 4: Configuration system
**Labels**: `epic:foundation`, `priority:high`

Sistema de configuración unificado (YAML + env vars + voice commands).

**Tasks:**
- [ ] `~/.jarvis/config.yaml` como config persistente
- [ ] Schema validado con `pydantic` 
- [ ] Voice config: "jarvis, cambiá la voz a Alloy", "jarvis, usá Groq para clasificación"
- [ ] Hot reload de config sin reiniciar
- [ ] `jarvis doctor` que verifica config, APIs, audio devices, modelos descargados

---

### EPIC 2 — Tool System

#### Issue 5: Tool registry — pluggable tool system
**Labels**: `epic:tools`, `priority:critical`

Base para todos los tools. Inspirado en Claude Code pero adaptado para voz.

```python
class VoiceTool:
    name: str
    description: str          # Lo que le pasamos a Claude
    voice_triggers: list[str] # Frases naturales que activan este tool
    requires_confirmation: bool
    
    async def execute(self, params: dict) -> ToolResult
    def summarize_result(self, result: ToolResult) -> str  # Para TTS
```

**Tasks:**
- [ ] Crear `core/tools/base.py` con `VoiceTool` base class
- [ ] Crear `core/tools/registry.py` — registro y descubrimiento de tools
- [ ] Tool result → TTS summarizer pipeline
- [ ] Tool execution con timeout y error handling
- [ ] Logging de tool calls para debugging

---

#### Issue 6: BashTool — execute shell commands via voice
**Labels**: `epic:tools`, `priority:high`

```
Usuario: "corré npm test"
Usuario: "instalá la dependencia axios"
Usuario: "mostrá el log de docker"
```

**Tasks:**
- [ ] `core/tools/bash_tool.py` con subprocess + streaming output
- [ ] Safety gate: lista de comandos peligrosos requieren confirmación por voz
- [ ] Output streaming → lexer → TTS (el usuario escucha el output en tiempo real)
- [ ] Timeout configurable
- [ ] Working directory awareness (sabe en qué directorio estás)
- [ ] Comandos interactivos: detectar prompts y preguntar al usuario

**Latency impact**: streaming de output — el usuario escucha el output mientras se ejecuta

---

#### Issue 7: FileReadTool — read and summarize files via voice
**Labels**: `epic:tools`, `priority:high`

```
Usuario: "leé el archivo main.py"
Usuario: "explicame qué hace el archivo de configuración"
Usuario: "mostrá las primeras 50 líneas de app.ts"
```

**Tasks:**
- [ ] `core/tools/file_read_tool.py`
- [ ] Nunca leer el archivo completo en voz — siempre resumir con LLM
- [ ] Para archivos grandes: chunking inteligente, resumir sección relevante
- [ ] Soporte para imágenes (descripción por voz), PDFs (summary), código (explain)
- [ ] "leé el archivo" → Claude lo lee y explica en lenguaje natural

---

#### Issue 8: FileWriteTool — create files via voice dictation
**Labels**: `epic:tools`, `priority:high`

```
Usuario: "creá un archivo llamado utils.py con una función que convierte celsius a fahrenheit"
Usuario: "creá el archivo README con lo que acabamos de hacer"
```

**Tasks:**
- [ ] `core/tools/file_write_tool.py`
- [ ] Confirmación por voz antes de escribir ("¿Confirmo que creo utils.py?")
- [ ] Preview verbal del contenido antes de escribir
- [ ] Soporte para templates ("creá un componente React llamado Button")

---

#### Issue 9: FileEditTool — edit files via voice description
**Labels**: `epic:tools`, `priority:high`

```
Usuario: "en main.py, cambiá la función login para que use JWT"
Usuario: "agregá validación de email a la función register"
Usuario: "refactorizá el for loop en línea 45 para usar list comprehension"
```

**Tasks:**
- [ ] `core/tools/file_edit_tool.py`
- [ ] Claude genera el diff, Jarvis lo aplica
- [ ] Confirmación verbal del cambio propuesto antes de aplicar
- [ ] Undo por voz: "deshacé el último cambio"
- [ ] Diff summary por voz antes y después

---

#### Issue 10: SearchTool — voice code search (grep + glob)
**Labels**: `epic:tools`, `priority:high`

```
Usuario: "buscá dónde se usa la función authenticate"
Usuario: "encontrá todos los archivos TypeScript con useEffect"
Usuario: "buscá TODO comments en el proyecto"
```

**Tasks:**
- [ ] `core/tools/search_tool.py` con ripgrep (`rg`) bajo el capó
- [ ] Glob para file patterns, Grep para content search
- [ ] Resultados resumidos por voz: "Encontré 5 archivos. El más relevante es..."
- [ ] "andá al resultado 1" → abre el archivo en el editor configurado

---

#### Issue 11: GitTool — complete git workflow via voice
**Labels**: `epic:tools`, `priority:high`

```
Usuario: "hace commit con el mensaje 'agrego autenticación JWT'"
Usuario: "creá una branch llamada feature/login"
Usuario: "mostrá el diff de lo que cambié"
Usuario: "hace push y abrí un PR"
Usuario: "qué cambié en los últimos 3 commits"
```

**Tasks:**
- [ ] `core/tools/git_tool.py` — wrapper de git con output summarizado
- [ ] Conventional commits por voz
- [ ] Diff summary vocal: "Modificaste 3 archivos. En main.py agregaste..."
- [ ] PR creation flow por voz (requiere `gh` CLI)
- [ ] Confirmación por voz para operaciones destructivas (reset, force push)
- [ ] Status summary: "Tenés 5 archivos modificados y 2 sin trackear"

---

#### Issue 12: WebFetchTool — fetch URLs and summarize content
**Labels**: `epic:tools`, `priority:medium`

```
Usuario: "buscá cómo usar la API de Stripe para pagos recurrentes"
Usuario: "abrí la documentación de FastAPI y explicame cómo funciona el middleware"
```

**Tasks:**
- [ ] `core/tools/web_fetch_tool.py`
- [ ] HTML → text extraction (beautifulsoup4)
- [ ] Summarización inteligente: solo la info relevante en voz
- [ ] Cache de URLs fetched en la sesión

---

### EPIC 3 — Voice UX

#### Issue 13: Voice Command Registry — natural language to action mapping
**Labels**: `epic:voice-ux`, `priority:critical`

Sistema que mapea frases naturales a herramientas sin pasar por el LLM (zero-latency para comandos conocidos).

```python
VOICE_COMMANDS = {
    "hace commit": GitTool(action="commit"),
    "corré los tests": BashTool(cmd="npm test"),
    "guardá el archivo": FileWriteTool(mode="save"),
    "deshacé eso": FileEditTool(action="undo"),
    "mostrá el diff": GitTool(action="diff"),
}
```

**Tasks:**
- [ ] `core/voice/command_registry.py`
- [ ] Fuzzy matching para variaciones naturales del idioma
- [ ] Soporte multi-idioma (español/inglés)
- [ ] Comandos configurables por usuario en `~/.jarvis/commands.yaml`
- [ ] Fallback a LLM cuando no hay match en el registro

**Latency impact**: CRÍTICO — comandos conocidos se ejecutan sin llamada a la API

---

#### Issue 14: Voice Permission System — approval for dangerous operations
**Labels**: `epic:voice-ux`, `priority:critical`

Extensión del sistema existente para cubrir todas las operaciones de coding.

```
Jarvis: "Esto va a eliminar 3 archivos permanentemente. ¿Confirmás?"
Usuario: "sí, confirmo" | "no, cancelá"
```

**Tasks:**
- [ ] Extender `adapters/llm/gemini_summarizer.py` para operations de coding
- [ ] Clasificar operaciones: SAFE | REQUIRES_CONFIRM | REQUIRES_EXPLAIN
- [ ] Timeout en el prompt de confirmación (default: 10s → cancela)
- [ ] "modo experto" que reduce confirmaciones para usuarios avanzados
- [ ] Log de operaciones confirmadas/canceladas

---

#### Issue 15: Voice Skill System — reusable voice workflows
**Labels**: `epic:voice-ux`, `priority:high`

Skills son flujos de trabajo reutilizables activados por voz. Inspirado en Claude Code skills.

```yaml
# ~/.jarvis/skills/new-component.yaml
name: "nuevo componente React"
trigger: "creá un componente (llamado )?{name}"
steps:
  - FileWriteTool: "src/components/{name}/{name}.tsx"
  - FileWriteTool: "src/components/{name}/{name}.test.tsx"
  - FileWriteTool: "src/components/{name}/index.ts"
confirm: true
```

**Tasks:**
- [ ] `core/skills/` — loader y executor de skills YAML
- [ ] Variable extraction desde voice input (nombre del componente, etc.)
- [ ] Skills built-in: new-component, new-api-route, new-test, git-feature-branch
- [ ] "jarvis, enseñame un skill nuevo" — crea skill desde descripción vocal
- [ ] Skill discovery: "jarvis, qué skills tenés?"

---

#### Issue 16: Streaming TTS pipeline — speak as Claude generates
**Labels**: `epic:voice-ux`, `priority:critical`

El sistema actual espera a que el lexer acumule una oración completa. Optimizar para hablar el primer chunk tan pronto como llegue del API.

**Tasks:**
- [ ] Modificar `poc_lexer.py` para emitir chunks más pequeños (< 50ms acumulación)
- [ ] Pipeline: API chunk → lexer → TTS sin buffering innecesario
- [ ] Sentence boundary detection más agresivo para TTS inmediato
- [ ] Adjustable chunk size via config: `MIN_TTS_CHUNK_CHARS = 30`
- [ ] Barge-in sigue funcionando durante streaming

**Latency impact**: CRÍTICO — reduce latencia percibida de segundos a milliseconds

---

#### Issue 17: Voice session context — "estás trabajando en X"
**Labels**: `epic:voice-ux`, `priority:high`

Jarvis debe anunciar el contexto de la sesión y mantenerlo actualizado.

```
Startup: "Jarvis listo. Proyecto: my-app. Branch: feature/login. 
          Tenés 3 archivos modificados sin commit."
```

**Tasks:**
- [ ] `core/context/session_context.py` — rastrea proyecto, branch, archivos abiertos
- [ ] Anuncio de contexto al inicio de sesión
- [ ] Auto-detección de proyecto (package.json, pyproject.toml, Cargo.toml, etc.)
- [ ] "jarvis, en qué estamos?" → resumen vocal del estado actual
- [ ] Notificación vocal cuando hay cambios de branch, conflictos, etc.

---

#### Issue 18: Barge-in for tool execution — interrupt any running task
**Labels**: `epic:voice-ux`, `priority:high`

El barge-in actual interrumpe el TTS. Extender para interrumpir tool execution.

**Tasks:**
- [ ] Tool execution en proceso cancellable (asyncio.Task con CancelledError)
- [ ] Barge-in signal → cancela tool + TTS + pregunta qué hacer
- [ ] "jarvis, pará" → cancela todo inmediatamente
- [ ] Confirmación verbal de cancelación: "Cancelé el comando. ¿Qué querés hacer?"

---

### EPIC 4 — Latency Zero

#### Issue 19: Intent pre-classifier — zero-latency command routing
**Labels**: `epic:latency`, `priority:critical`

Clasificador local (sin API call) que decide si el comando va a:
1. **Registry directo** — comando conocido, ejecución inmediata
2. **Claude API** — razonamiento complejo necesario
3. **Local tool** — operación de sistema directa

**Tasks:**
- [ ] Modelo de clasificación local: `mlx-community/phi-3-mini-4k-instruct-mlx` o similar
- [ ] Entrenado/finetuned en ~200 ejemplos de comandos de voz de programación
- [ ] Latencia objetivo: < 50ms para clasificación
- [ ] Fallback: si el clasificador tiene baja confianza → siempre Claude API
- [ ] Métricas: loguear accuracy del clasificador en producción

**Latency impact**: CRÍTICO — elimina llamada API para ~70% de comandos

---

#### Issue 20: Parallel STT + classification pipeline
**Labels**: `epic:latency`, `priority:high`

Mientras el STT transcribe, lanzar el clasificador en paralelo con los primeros tokens.

**Tasks:**
- [ ] Streaming STT: MLX Whisper en modo streaming (si soportado)
- [ ] Clasificación parcial con primeros N tokens de la transcripción
- [ ] Pipeline: audio chunk → STT partial → classifier → pre-load tool
- [ ] Benchmark antes/después: medir latencia end-to-end

**Latency impact**: ALTO — overlapping STT y clasificación

---

#### Issue 21: Response streaming — first token to TTS in < 200ms
**Labels**: `epic:latency`, `priority:critical`

**Target**: Usuario termina de hablar → Jarvis empieza a responder en < 200ms.

**Tasks:**
- [ ] Medir latencia actual end-to-end (STT finish → TTS start)
- [ ] Identificar y eliminar bottlenecks en el pipeline
- [ ] Claude API: usar `anthropic.stream()` con manejo de primer chunk
- [ ] TTS: mac_say como default (zero overhead), Edge TTS como fallback
- [ ] Benchmark continuo: alert si latencia > 500ms

**Latency impact**: CRÍTICO — latencia percibida es lo que mide el usuario

---

#### Issue 22: Model pre-warming at startup
**Labels**: `epic:latency`, `priority:high`

Cargar todos los modelos locales al arrancar, no cuando se necesitan.

**Tasks:**
- [ ] MLX Whisper: pre-cargar al startup
- [ ] Intent classifier: pre-cargar al startup  
- [ ] Warm-up call a Claude API para pre-establecer conexión HTTP/2
- [ ] Startup time objetivo: < 3 segundos
- [ ] Progress indicator vocal durante startup: "Cargando modelos..."
- [ ] Lazy loading para modelos opcionales (Edge TTS, Kokoro, etc.)

---

#### Issue 23: Groq fast-path for classification and simple responses
**Labels**: `epic:latency`, `priority:high`

Groq (llama-3.3-70b) tiene ~300ms de latencia vs ~1s de Claude. Usarlo para:
- Clasificación de intento cuando el local model no es suficiente
- Respuestas simples que no requieren razonamiento profundo
- Resúmenes rápidos de tool results

**Tasks:**
- [ ] Adaptar `groq_summarizer.py` para routing inteligente
- [ ] Reglas de routing: simple/fast → Groq, complex/code → Claude
- [ ] A/B testing de respuestas Groq vs Claude para optimizar routing
- [ ] Fallback: si Groq falla → Claude API

---

### EPIC 5 — Intelligence

#### Issue 24: Code context awareness — track project state
**Labels**: `epic:intelligence`, `priority:high`

Jarvis debe saber en todo momento en qué estás trabajando.

```python
@dataclass
class CodeContext:
    project_root: Path
    language: str          # Python, TypeScript, Go, etc.
    framework: str         # FastAPI, React, etc.
    current_file: Path
    current_function: str
    git_branch: str
    modified_files: list[Path]
    recent_errors: list[str]
```

**Tasks:**
- [ ] `core/context/code_context.py` — detección automática de contexto
- [ ] Watch de filesystem: detectar qué archivo está siendo editado
- [ ] Integración con git: branch, modified files, last commit
- [ ] Contexto inyectado automáticamente en cada prompt a Claude
- [ ] "jarvis, en qué función estoy?" → respuesta inmediata sin API call

---

#### Issue 25: Smart output summarization — coding-specific
**Labels**: `epic:intelligence`, `priority:high`

El summarizer actual es genérico. Crear uno específico para output de coding.

**Tasks:**
- [ ] Detectar tipo de output: error, test result, build output, git log, etc.
- [ ] Template de summarización por tipo:
  - Error: "Hay un TypeError en línea 45 de auth.py. El problema es..."
  - Tests: "Pasaron 47 de 50 tests. Los 3 que fallaron son..."
  - Build: "Build exitoso en 2.3 segundos. Bundle size: 450KB"
  - Git log: "Los últimos 3 commits agregan autenticación, tests y documentación"
- [ ] Nunca leer stack traces completos — extraer la línea relevante

---

#### Issue 26: Error pattern detection and voice alert
**Labels**: `epic:intelligence`, `priority:medium`

Detectar errores en el output de herramientas y alertar proactivamente.

**Tasks:**
- [ ] Watcher de output: detectar patterns de error (stderr, exit codes, "Error:", "Exception:")
- [ ] Alert vocal inmediato sin esperar que el usuario pregunte
- [ ] Clasificar severidad: WARNING (mencionar), ERROR (interrumpir y explicar), CRITICAL (pedir confirmación)
- [ ] Sugerir fix automáticamente cuando hay un error conocido

---

#### Issue 27: Test result summarization — voice-friendly
**Labels**: `epic:intelligence`, `priority:medium`

```
Usuario: "corré los tests"
Jarvis: "Corrí 50 tests en 3.2 segundos. Pasaron 48, fallaron 2. 
         El primer error está en UserService en el test de login: 
         esperaba 200 pero recibió 401. ¿Querés que lo revise?"
```

**Tasks:**
- [ ] Parsers para Jest, pytest, Go test, Cargo test
- [ ] Summary template: N passed, M failed, tiempo total
- [ ] Para failures: extraer test name + error message (no stack trace)
- [ ] "revisá el primer error" → FileReadTool + análisis de la línea fallida

---

### EPIC 6 — Advanced

#### Issue 28: Multi-agent voice orchestration
**Labels**: `epic:advanced`, `priority:medium`

```
Usuario: "mientras escribís los tests, buscá si hay una librería mejor para esto"
```

Lanzar sub-agentes en paralelo via voz.

**Tasks:**
- [ ] `core/agents/` — sub-agent spawning
- [ ] Cada agente tiene su propio tool context y conversación
- [ ] Orquestador vocal: reporta progreso de múltiples agentes
- [ ] "agente 1: terminó. Agente 2: todavía trabajando..."
- [ ] Cancelación por voz de agentes individuales

---

#### Issue 29: MCP server integration via voice
**Labels**: `epic:advanced`, `priority:medium`

Soportar MCP servers como extensiones de los tools de Jarvis.

```
Usuario: "conectate al servidor de Linear y mostrá los tickets del sprint"
```

**Tasks:**
- [ ] `core/mcp/` — MCP client implementation (SDK Python)
- [ ] Configuración de MCP servers en `~/.jarvis/mcp.yaml`
- [ ] Auto-discovery de tools disponibles en cada MCP server
- [ ] Voice triggers para MCP tools
- [ ] Jarvis como MCP server (exponerse a Claude Code CLI)

---

#### Issue 30: Session memory and resume
**Labels**: `epic:advanced`, `priority:medium`

```
Usuario: "jarvis, ¿qué estábamos haciendo ayer?"
Jarvis: "Estabas implementando autenticación JWT. Terminaste el middleware 
         pero te faltaba el refresh token. ¿Seguimos?"
```

**Tasks:**
- [ ] `core/memory/` — persistencia de conversación entre sesiones
- [ ] Session summary al cerrar (qué se hizo, qué falta)
- [ ] Resume: "jarvis, continuá donde estábamos"
- [ ] Memory search: "jarvis, cómo resolvimos el problema de CORS la semana pasada"
- [ ] Integración con Engram (sistema de memoria del orquestador)

---

#### Issue 31: LSP integration for code intelligence
**Labels**: `epic:advanced`, `priority:low`

Language Server Protocol para code intelligence sin abrir un editor.

**Tasks:**
- [ ] `core/lsp/` — LSP client (python-lsp-jsonrpc o similar)
- [ ] Go-to-definition por voz: "andá a la definición de authenticate"
- [ ] Find references: "dónde se usa esta función"
- [ ] Hover info: "qué hace este método"
- [ ] Auto-detectar LSP server según lenguaje del proyecto

---

#### Issue 32: Claude Code CLI as PTY backend (hybrid mode)
**Labels**: `epic:advanced`, `priority:low`

Modo híbrido donde Jarvis wrappea el Claude Code CLI en lugar de llamar a la API directamente. Para usuarios que quieren la experiencia completa de Claude Code + control por voz.

**Tasks:**
- [ ] PTY adapter para Claude Code CLI (ya existe para Gemini CLI — adaptar)
- [ ] Patch del lexer para el output format de Claude Code
- [ ] Tool calls de Claude Code interceptados y anunciados por voz
- [ ] Confirmaciones de permisos de Claude Code → voice approval
- [ ] Modo de selección: `jarvis --mode pty --cli claude-code`

---

## Priority Matrix

| Priority | Issues |
|----------|--------|
| 🔴 Critical | #1, #2, #5, #13, #16, #19, #21 |
| 🟠 High | #3, #4, #6, #7, #8, #9, #10, #11, #14, #15, #17, #18, #20, #22, #23, #24, #25 |
| 🟡 Medium | #12, #26, #27, #28, #29, #30 |
| 🟢 Low | #31, #32 |

## Sprint 1 (MVP Voice Coding CLI)

Issues: #1, #2, #5, #6, #11, #13, #16, #21

**Goal**: Jarvis habla con Claude API, puede ejecutar shell commands y git, y la latencia es mínima.

## Sprint 2 (Tool System Complete)

Issues: #3, #4, #7, #8, #9, #10, #14, #15, #19

**Goal**: Todas las herramientas de coding básicas disponibles por voz.

## Sprint 3 (Intelligence + Latency)

Issues: #17, #18, #20, #22, #23, #24, #25, #26, #27

**Goal**: Jarvis entiende el contexto del código y responde en < 200ms.

## Sprint 4 (Advanced)

Issues: #28, #29, #30, #31, #32

**Goal**: Multi-agente, MCP, memoria persistente, LSP.
