#!/usr/bin/env bash
# Crea todas las issues del roadmap JARVIS Voice Coding CLI
# Uso: bash create_issues.sh
# Requiere: gh auth login (ejecutar una vez antes)

set -e
REPO="cr8297408/J.A.R.V.I.S"

echo "Creando labels..."
gh label create "epic:foundation"     --color "#0075ca" --description "Core CLI infrastructure" --repo $REPO 2>/dev/null || true
gh label create "epic:tools"          --color "#e4e669" --description "Voice-adapted coding tools" --repo $REPO 2>/dev/null || true
gh label create "epic:voice-ux"       --color "#d93f0b" --description "Voice UX for coding" --repo $REPO 2>/dev/null || true
gh label create "epic:latency"        --color "#0e8a16" --description "Latency optimizations" --repo $REPO 2>/dev/null || true
gh label create "epic:intelligence"   --color "#5319e7" --description "Code context intelligence" --repo $REPO 2>/dev/null || true
gh label create "epic:advanced"       --color "#b60205" --description "Advanced features" --repo $REPO 2>/dev/null || true
gh label create "priority:critical"   --color "#b60205" --description "Must have for MVP" --repo $REPO 2>/dev/null || true
gh label create "priority:high"       --color "#d93f0b" --description "Sprint deliverable" --repo $REPO 2>/dev/null || true
gh label create "priority:medium"     --color "#e4e669" --description "Next sprint" --repo $REPO 2>/dev/null || true
gh label create "priority:low"        --color "#0075ca" --description "Backlog" --repo $REPO 2>/dev/null || true

echo "Creando milestones..."
gh api repos/$REPO/milestones -f title="M1: Foundation" -f description="Jarvis como CLI standalone con Claude API" 2>/dev/null || true
gh api repos/$REPO/milestones -f title="M2: Tool System" -f description="Herramientas de coding adaptadas para voz" 2>/dev/null || true
gh api repos/$REPO/milestones -f title="M3: Voice UX" -f description="UX de voz específico para programar" 2>/dev/null || true
gh api repos/$REPO/milestones -f title="M4: Latency Zero" -f description="Optimizaciones de latencia agresivas" 2>/dev/null || true
gh api repos/$REPO/milestones -f title="M5: Intelligence" -f description="Conciencia de contexto de código" 2>/dev/null || true
gh api repos/$REPO/milestones -f title="M6: Advanced" -f description="Multi-agente, MCP, LSP" 2>/dev/null || true

echo "Creando issues..."

# ── EPIC 1: Foundation ─────────────────────────────────────────────────────

gh issue create --repo $REPO \
  --title "[EPIC-1] Refactor entry point as standalone \`jarvis\` CLI" \
  --label "epic:foundation,priority:critical" \
  --body "## Objetivo
Jarvis debe ser instalable como comando global (\`pip install -e .\`) y soportar subcomandos.

## Tasks
- [ ] Crear \`pyproject.toml\` con entry point \`jarvis = main:cli\`
- [ ] Refactorizar \`main.py\` con subcomandos: \`jarvis start\`, \`jarvis config\`, \`jarvis doctor\`
- [ ] Agregar \`--backend\` flag: \`claude\` | \`gemini\` | \`groq\`
- [ ] Help text por voz: decir 'jarvis help' habla los comandos disponibles
- [ ] Validación de env vars al startup con mensajes de error claros por voz

## Latency impact
Ninguno (infraestructura pura)

## Definition of Done
- \`pipx install .\` instala el comando \`jarvis\`
- \`jarvis start\` arranca el sistema de voz
- \`jarvis doctor\` verifica APIs, audio, modelos"

gh issue create --repo $REPO \
  --title "[EPIC-2] Claude API direct integration — replace PTY with streaming API" \
  --label "epic:foundation,priority:critical" \
  --body "## Objetivo
Reemplazar el PTY wrapper de Gemini CLI con llamadas directas a la Claude API con streaming. El PTY queda como fallback opcional.

## Tasks
- [ ] Crear \`adapters/llm/claude_api_adapter.py\` con \`anthropic\` SDK
- [ ] Implementar streaming response handler (chunks → lexer existente)
- [ ] Adaptar \`poc_lexer.py\` para manejar API response (no PTY output)
- [ ] Tool use loop: detectar tool calls en el stream, ejecutar, enviar result
- [ ] Mantener historial de conversación en memoria (multi-turn)
- [ ] Configurar modelos: \`claude-opus-4-6\` para razonamiento, \`claude-haiku-4-5\` para clasificación

## Latency impact
**CRÍTICO** — streaming desde primer token, TTS empieza antes de que termine la respuesta completa.

## Definition of Done
- Usuario habla → Jarvis responde via Claude API en streaming
- Primer token hablado en < 500ms desde fin del speech
- Tool calls detectados y ejecutados en el loop"

gh issue create --repo $REPO \
  --title "[EPIC-3] Multi-backend CLI adapter (API mode + PTY mode)" \
  --label "epic:foundation,priority:high" \
  --body "## Objetivo
Soportar tres modos de operación con la misma interfaz interna.

\`\`\`
MODE=api       → llama directamente Claude/Gemini API (mínima latencia)
MODE=pty       → wrappea un CLI externo (Claude Code CLI, Gemini CLI)
MODE=hybrid    → API para reasoning, PTY para tool execution
\`\`\`

## Tasks
- [ ] Crear \`core/backend/\` con \`BackendBase\`, \`APIBackend\`, \`PTYBackend\`
- [ ] Factory pattern seleccionable via \`JARVIS_MODE\` env var o \`--mode\` flag
- [ ] Ambos backends emiten eventos al mismo lexer/TTS pipeline
- [ ] Tests de smoke para cada modo

## Definition of Done
- \`jarvis start --mode api\` usa Claude API directamente
- \`jarvis start --mode pty --cli gemini\` wrappea Gemini CLI
- Misma experiencia de voz en ambos modos"

gh issue create --repo $REPO \
  --title "[EPIC-4] Unified configuration system (YAML + env vars + voice)" \
  --label "epic:foundation,priority:high" \
  --body "## Objetivo
Sistema de configuración unificado con soporte para cambios por voz.

## Tasks
- [ ] \`~/.jarvis/config.yaml\` como config persistente
- [ ] Schema validado con \`pydantic\`
- [ ] Voice config: 'jarvis, cambiá la voz a Alloy', 'jarvis, usá Groq para clasificación'
- [ ] Hot reload de config sin reiniciar el proceso
- [ ] \`jarvis doctor\` verifica config, APIs keys, audio devices, modelos descargados
- [ ] Config por proyecto: \`.jarvis.yaml\` en el root del proyecto

## Definition of Done
- Config válida al startup, errores claros si falta algo
- Cambios de config por voz persisten entre sesiones"

# ── EPIC 2: Tool System ────────────────────────────────────────────────────

gh issue create --repo $REPO \
  --title "[EPIC-5] Tool registry — pluggable voice tool system" \
  --label "epic:tools,priority:critical" \
  --body "## Objetivo
Base para todos los tools de coding. Inspirado en Claude Code pero adaptado para voz.

## Interface
\`\`\`python
class VoiceTool:
    name: str
    description: str          # Para el system prompt de Claude
    voice_triggers: list[str] # Frases naturales que activan este tool
    requires_confirmation: bool

    async def execute(self, params: dict) -> ToolResult
    def summarize_result(self, result: ToolResult) -> str  # Para TTS
\`\`\`

## Tasks
- [ ] Crear \`core/tools/base.py\` con \`VoiceTool\` base class y \`ToolResult\`
- [ ] Crear \`core/tools/registry.py\` — registro y auto-discovery de tools
- [ ] Tool result → voice summarizer pipeline
- [ ] Tool execution con timeout configurable y error handling
- [ ] Logging de tool calls para debugging y métricas

## Definition of Done
- Nueva tool se registra decorando la clase con \`@registry.register\`
- Tools disponibles se inyectan automáticamente en el system prompt de Claude"

gh issue create --repo $REPO \
  --title "[EPIC-6] BashTool — execute shell commands via voice" \
  --label "epic:tools,priority:high" \
  --body "## Objetivo
Ejecutar comandos de shell por voz con streaming output.

## Ejemplos de uso
\`\`\`
'corré npm test'
'instalá la dependencia axios'
'mostrá el log de docker'
'compilá el proyecto'
\`\`\`

## Tasks
- [ ] \`core/tools/bash_tool.py\` con subprocess + streaming output
- [ ] Safety gate: lista de comandos peligrosos requieren confirmación por voz (rm -rf, DROP TABLE, etc.)
- [ ] Output streaming → lexer → TTS (escuchar output en tiempo real)
- [ ] Timeout configurable (default: 30s)
- [ ] Working directory awareness: sabe en qué dir estás
- [ ] Detectar prompts interactivos y preguntar al usuario

## Latency impact
**ALTO** — streaming de output: el usuario escucha mientras se ejecuta

## Definition of Done
- 'corré npm test' ejecuta y narra el output en tiempo real
- Comandos peligrosos requieren confirmación vocal antes de ejecutar"

gh issue create --repo $REPO \
  --title "[EPIC-7] FileReadTool — read and intelligently summarize files via voice" \
  --label "epic:tools,priority:high" \
  --body "## Objetivo
Leer archivos de código y resumirlos de forma vocal inteligente. NUNCA leer código crudo.

## Ejemplos de uso
\`\`\`
'leé el archivo main.py'
'explicame qué hace el archivo de configuración'
'mostrá las primeras 50 líneas de app.ts'
'qué hace la función authenticate?'
\`\`\`

## Tasks
- [ ] \`core/tools/file_read_tool.py\`
- [ ] Nunca leer archivo completo en voz — siempre pasar por LLM para resumir
- [ ] Para archivos grandes: chunking inteligente, resumir sección relevante
- [ ] Soporte para imágenes (descripción), PDFs (summary), Jupyter notebooks
- [ ] Query específica: 'qué hace la función X' → extrae y explica solo esa función

## Definition of Done
- 'leé main.py' → Jarvis explica qué hace el archivo en 2-3 oraciones
- Para archivos > 1000 líneas, pregunta qué parte querés escuchar"

gh issue create --repo $REPO \
  --title "[EPIC-8] FileWriteTool — create files via voice dictation" \
  --label "epic:tools,priority:high" \
  --body "## Objetivo
Crear archivos nuevos dictándolos por voz.

## Ejemplos de uso
\`\`\`
'creá un archivo llamado utils.py con una función que convierte celsius a fahrenheit'
'creá el archivo README con lo que acabamos de hacer'
'generá un componente React Button básico'
\`\`\`

## Tasks
- [ ] \`core/tools/file_write_tool.py\`
- [ ] Confirmación por voz antes de escribir: '¿Confirmo que creo utils.py con X?'
- [ ] Preview verbal del contenido antes de escribir (descripción, no el código)
- [ ] Soporte para templates de proyecto (componente React, route FastAPI, etc.)
- [ ] Undo: 'deshacé eso' → elimina el archivo recién creado

## Definition of Done
- Usuario describe el archivo → Claude lo genera → Jarvis confirma y lo crea
- Archivo queda en el filesystem, Jarvis confirma la creación"

gh issue create --repo $REPO \
  --title "[EPIC-9] FileEditTool — edit existing files via voice description" \
  --label "epic:tools,priority:high" \
  --body "## Objetivo
Modificar archivos existentes describiendo los cambios en lenguaje natural.

## Ejemplos de uso
\`\`\`
'en main.py, cambiá la función login para que use JWT'
'agregá validación de email a la función register'
'refactorizá el for loop en línea 45 para usar list comprehension'
'reemplazá todos los var por const en el archivo'
\`\`\`

## Tasks
- [ ] \`core/tools/file_edit_tool.py\`
- [ ] Claude genera el diff, Jarvis lo aplica vía string replacement
- [ ] Descripción vocal del cambio propuesto ANTES de aplicar
- [ ] Confirmación: '¿Aplicás el cambio?' → 'sí' | 'no, cambiá X'
- [ ] Undo por voz: 'deshacé el último cambio' → revert via git
- [ ] Diff summary vocal después de aplicar

## Definition of Done
- Usuario describe cambio → Jarvis aplica el diff → confirma qué cambió
- Undo disponible en la misma sesión"

gh issue create --repo $REPO \
  --title "[EPIC-10] SearchTool — voice code search (ripgrep + glob)" \
  --label "epic:tools,priority:high" \
  --body "## Objetivo
Buscar en el código por voz y narrar resultados relevantes.

## Ejemplos de uso
\`\`\`
'buscá dónde se usa la función authenticate'
'encontrá todos los archivos TypeScript con useEffect'
'buscá TODO comments en el proyecto'
'encontrá archivos modificados en las últimas 24 horas'
\`\`\`

## Tasks
- [ ] \`core/tools/search_tool.py\` con \`rg\` (ripgrep) bajo el capó
- [ ] Glob para file patterns, Grep para content search
- [ ] Resultados resumidos por voz: 'Encontré 5 archivos. El más relevante es...'
- [ ] 'andá al resultado 1' → abre en editor configurado (\$EDITOR)
- [ ] Fuzzy matching en nombres de función/archivo

## Definition of Done
- Búsqueda por voz retorna resultados en < 1 segundo
- Jarvis narra los top 3 resultados relevantes"

gh issue create --repo $REPO \
  --title "[EPIC-11] GitTool — complete git workflow via voice" \
  --label "epic:tools,priority:high" \
  --body "## Objetivo
Workflow completo de git controlado por voz.

## Ejemplos de uso
\`\`\`
'hace commit con mensaje agrego autenticación JWT'
'creá una branch llamada feature/login'
'mostrá el diff de lo que cambié'
'hace push y abrí un PR'
'qué cambié en los últimos 3 commits'
'quién cambió esta línea'
\`\`\`

## Tasks
- [ ] \`core/tools/git_tool.py\` — wrapper con output summarizado
- [ ] Conventional commits por voz (detecta tipo: feat/fix/refactor/etc.)
- [ ] Diff summary vocal: 'Modificaste 3 archivos. En main.py agregaste...'
- [ ] PR creation flow por voz (usa \`gh\` CLI)
- [ ] Confirmación por voz para operaciones destructivas (reset, force push)
- [ ] Status summary: 'Tenés 5 archivos modificados y 2 sin trackear'
- [ ] Git blame por voz: 'quién cambió la función login y cuándo'

## Definition of Done
- Workflow completo feat-branch → commit → push → PR por voz
- Operaciones destructivas requieren doble confirmación vocal"

gh issue create --repo $REPO \
  --title "[EPIC-12] WebFetchTool — fetch URLs and summarize content via voice" \
  --label "epic:tools,priority:medium" \
  --body "## Objetivo
Buscar en la web y resumir documentación por voz.

## Ejemplos de uso
\`\`\`
'buscá cómo usar la API de Stripe para pagos recurrentes'
'abrí la doc de FastAPI y explicame cómo funciona el middleware'
\`\`\`

## Tasks
- [ ] \`core/tools/web_fetch_tool.py\`
- [ ] HTML → text extraction (beautifulsoup4)
- [ ] Summarización inteligente: solo info relevante para la pregunta
- [ ] Cache de URLs fetched en la sesión (no re-fetch)
- [ ] Timeout de 10s con fallback vocal

## Definition of Done
- URL fetched y resumida en < 5 segundos
- Jarvis narra solo la sección relevante de la documentación"

# ── EPIC 3: Voice UX ───────────────────────────────────────────────────────

gh issue create --repo $REPO \
  --title "[EPIC-13] Voice Command Registry — zero-latency command routing" \
  --label "epic:voice-ux,priority:critical" \
  --body "## Objetivo
Mapear frases naturales a acciones SIN pasar por el LLM. Latencia: 0ms adicional.

## Ejemplo de configuración
\`\`\`python
VOICE_COMMANDS = {
    'hace commit': GitTool(action='commit'),
    'corré los tests': BashTool(cmd='npm test'),
    'guardá el archivo': FileWriteTool(mode='save'),
    'deshacé eso': FileEditTool(action='undo'),
    'mostrá el diff': GitTool(action='diff'),
    'qué cambié': GitTool(action='status'),
}
\`\`\`

## Tasks
- [ ] \`core/voice/command_registry.py\`
- [ ] Fuzzy matching para variaciones naturales ('hace un commit', 'hacé commit', 'commit')
- [ ] Soporte multi-idioma (español/inglés en el mismo registro)
- [ ] Comandos configurables por usuario en \`~/.jarvis/commands.yaml\`
- [ ] Fallback a LLM cuando no hay match con confianza suficiente
- [ ] Métricas: log de qué porcentaje de comandos van al registry vs LLM

## Latency impact
**CRÍTICO** — elimina llamada API para ~60-70% de comandos frecuentes

## Definition of Done
- 'hace commit' ejecuta sin llamar a la API
- Registry customizable por usuario
- Fallback transparente al LLM cuando no hay match"

gh issue create --repo $REPO \
  --title "[EPIC-14] Voice Permission System — voice approval for dangerous operations" \
  --label "epic:voice-ux,priority:critical" \
  --body "## Objetivo
Extender el sistema de permisos existente para todas las operaciones de coding.

## Flow
\`\`\`
Jarvis: 'Esto va a eliminar 3 archivos permanentemente. ¿Confirmás?'
Usuario: 'sí, confirmo' | 'no, cancelá' | [silencio 10s → cancela automático]
\`\`\`

## Clasificación de operaciones
| Tipo | Acción |
|------|--------|
| SAFE | Ejecutar directo (leer, buscar) |
| REQUIRES_CONFIRM | Pedir 'sí/no' por voz |
| REQUIRES_EXPLAIN | Explicar qué va a pasar + confirmar |

## Tasks
- [ ] Extender sistema existente en \`adapters/llm/gemini_summarizer.py\`
- [ ] Clasificación automática de operaciones por nivel de riesgo
- [ ] Timeout en prompt de confirmación (10s → cancela)
- [ ] 'modo experto': reduce confirmaciones para devs avanzados
- [ ] Log de todas las operaciones confirmadas/canceladas

## Definition of Done
- Operaciones de escritura/delete siempre piden confirmación vocal
- Timeout automático cancela operaciones pendientes"

gh issue create --repo $REPO \
  --title "[EPIC-15] Voice Skill System — reusable voice coding workflows" \
  --label "epic:voice-ux,priority:high" \
  --body "## Objetivo
Skills son flujos de trabajo reutilizables activados por voz. Como los skills de Claude Code pero dictados.

## Ejemplo de skill YAML
\`\`\`yaml
name: 'nuevo componente React'
trigger: 'creá un componente (llamado )?{name}'
steps:
  - FileWriteTool: 'src/components/{name}/{name}.tsx'
  - FileWriteTool: 'src/components/{name}/{name}.test.tsx'
  - FileWriteTool: 'src/components/{name}/index.ts'
confirm: true
announce_completion: true
\`\`\`

## Built-in skills
- new-component (React/Vue/Angular)
- new-api-route (FastAPI/Express/Go)
- new-test (unit/integration)
- git-feature-branch (branch → commit → PR)
- code-review (analiza diff y reporta)

## Tasks
- [ ] \`core/skills/\` — loader y executor de skills YAML
- [ ] Variable extraction desde voice input con regex
- [ ] Skills built-in listos para usar
- [ ] 'jarvis, enseñame un skill nuevo' — crear skill desde descripción vocal
- [ ] 'jarvis, qué skills tenés?' → lista los disponibles por voz

## Definition of Done
- Skill se activa con frase natural
- Variables extraídas del comando de voz
- Skills customizables por el usuario"

gh issue create --repo $REPO \
  --title "[EPIC-16] Streaming TTS pipeline — speak as Claude generates" \
  --label "epic:voice-ux,priority:critical" \
  --body "## Objetivo
Hablar el primer chunk de la respuesta tan pronto como llegue del API, sin esperar la respuesta completa.

## Pipeline objetivo
\`\`\`
API chunk → lexer (< 30 chars) → TTS → speaker
[   ~50ms  ][       < 20ms      ][~0ms ][   ]
\`\`\`

## Tasks
- [ ] Modificar \`poc_lexer.py\` para emitir chunks más pequeños (threshold: 30 chars o primer punto)
- [ ] Eliminar buffers innecesarios entre lexer y TTS
- [ ] Sentence boundary detection agresivo para TTS inmediato
- [ ] Config: \`MIN_TTS_CHUNK_CHARS = 30\` (ajustable)
- [ ] Barge-in sigue funcionando durante streaming
- [ ] Benchmark: medir latencia actual vs target < 200ms

## Latency impact
**CRÍTICO** — reduce latencia percibida de 2-3 segundos a < 300ms

## Definition of Done
- Primera palabra hablada en < 300ms desde fin del speech del usuario
- Barge-in funciona durante respuesta streaming"

gh issue create --repo $REPO \
  --title "[EPIC-17] Voice session context announcer" \
  --label "epic:voice-ux,priority:high" \
  --body "## Objetivo
Jarvis sabe y anuncia en qué está trabajando el usuario.

## Startup announcement
\`\`\`
'Jarvis listo. Proyecto: my-app. Branch: feature/login.
Tenés 3 archivos modificados sin commit. ¿En qué arrancamos?'
\`\`\`

## Tasks
- [ ] \`core/context/session_context.py\` — estado de la sesión
- [ ] Anuncio de contexto al inicio de sesión
- [ ] Auto-detección de proyecto (package.json, pyproject.toml, Cargo.toml)
- [ ] 'jarvis, en qué estamos?' → resumen vocal del estado actual
- [ ] Notificaciones proactivas: branch changes, conflictos de merge, CI status

## Definition of Done
- Startup anuncia proyecto, branch y archivos modificados
- 'en qué estamos' retorna contexto completo en < 2 segundos"

gh issue create --repo $REPO \
  --title "[EPIC-18] Barge-in for tool execution — interrupt any running task" \
  --label "epic:voice-ux,priority:high" \
  --body "## Objetivo
Extender el barge-in existente (que interrumpe TTS) para cancelar también tool execution.

## Flow
\`\`\`
[Tool ejecutando] → usuario habla → barge-in detectado
→ cancela tool + TTS
→ 'Cancelé el comando. ¿Qué querés hacer?'
\`\`\`

## Tasks
- [ ] Tool execution como asyncio.Task cancellable
- [ ] Barge-in signal cancela: tool actual + TTS + pide nueva instrucción
- [ ] 'jarvis, pará' como comando de cancelación explícito
- [ ] Cleanup de resources al cancelar (cerrar procesos, archivos abiertos)
- [ ] Log de cancelaciones para debugging

## Definition of Done
- Cualquier task en ejecución cancellable diciendo 'pará' o con barge-in
- Sistema queda en estado limpio después de cancelación"

# ── EPIC 4: Latency ────────────────────────────────────────────────────────

gh issue create --repo $REPO \
  --title "[EPIC-19] Intent pre-classifier — zero-latency local command routing" \
  --label "epic:latency,priority:critical" \
  --body "## Objetivo
Modelo de clasificación LOCAL (sin API call) que decide el routing en < 50ms.

## Routing decisions
1. **Registry directo** — comando conocido → ejecución inmediata sin LLM
2. **Local tool** — operación de sistema simple → ejecutar sin LLM
3. **Claude API** — razonamiento complejo o code gen necesario

## Tasks
- [ ] Evaluar modelos: \`mlx-community/phi-3-mini-4k-instruct-mlx\` vs reglas simples
- [ ] Dataset de entrenamiento: ~300 ejemplos de comandos de voz de coding
- [ ] Latencia objetivo del classifier: < 50ms en Apple Silicon
- [ ] Fallback: si confianza < 0.8 → siempre Claude API
- [ ] Métricas: loguear accuracy del classifier en producción
- [ ] A/B test: classifier vs sin classifier en latencia end-to-end

## Latency impact
**CRÍTICO** — elimina API call para comandos simples (~60% de los casos)

## Definition of Done
- Comandos simples clasificados y ejecutados sin API call
- Latencia de clasificación < 50ms medida"

gh issue create --repo $REPO \
  --title "[EPIC-20] Parallel STT + intent detection pipeline" \
  --label "epic:latency,priority:high" \
  --body "## Objetivo
Lanzar clasificación de intento con los primeros tokens de la transcripción en paralelo al STT.

## Pipeline actual (secuencial)
\`\`\`
Audio → STT (completo) → Classifier → Tool execution
[  ~800ms  ]           [ ~50ms    ]
\`\`\`

## Pipeline objetivo (paralelo)
\`\`\`
Audio → STT partial (200ms) → Classifier START
     → STT complete        → Classifier RESULT → Tool execution
[  ~800ms total, classifier overlapped       ]
\`\`\`

## Tasks
- [ ] MLX Whisper en modo streaming si disponible, sino partial transcription
- [ ] Classifier recibe partial text y pre-carga el tool probable
- [ ] Si clasificación parcial correcta → tool ya cargado cuando STT termina
- [ ] Benchmark: latencia STT finish → tool start antes y después
- [ ] Fallback: si partial transcript es < 3 palabras → esperar completo

## Latency impact
**ALTO** — reduce latencia post-STT solapando con STT

## Definition of Done
- Pipeline paralelo implementado y benchmarkeado
- Mejora medible en latencia end-to-end"

gh issue create --repo $REPO \
  --title "[EPIC-21] Response streaming — first token to TTS in < 200ms" \
  --label "epic:latency,priority:critical" \
  --body "## Objetivo
**Target**: Usuario termina de hablar → Jarvis empieza a responder en < 200ms.

## Breakdown de latencia objetivo
\`\`\`
STT finish → classifier: 50ms
Classifier → API first request: 30ms
API first token: 80ms
First token → TTS start: 20ms
TTS → speaker: ~20ms (mac_say)
───────────────────────────────
Total: ~200ms
\`\`\`

## Tasks
- [ ] Medir latencia actual end-to-end con timestamps en cada etapa
- [ ] Identificar y eliminar bottlenecks con profiling
- [ ] Claude API: usar \`anthropic.stream()\` asegurar manejo correcto del primer chunk
- [ ] TTS: mac_say como default (zero overhead), Edge TTS como fallback
- [ ] Agregar métricas de latencia al log: P50, P95, P99
- [ ] Alert si latencia > 500ms de forma consistente

## Definition of Done
- Latencia medida P50 < 200ms
- Dashboard de latencia en logs"

gh issue create --repo $REPO \
  --title "[EPIC-22] Model pre-warming — load all local models at startup" \
  --label "epic:latency,priority:high" \
  --body "## Objetivo
Cargar todos los modelos locales en background al arrancar, no cuando se necesitan por primera vez.

## Tasks
- [ ] MLX Whisper: pre-cargar en background thread al startup
- [ ] Intent classifier: pre-cargar en background thread
- [ ] Warm-up call a Claude API para pre-establecer conexión HTTP/2
- [ ] Startup time objetivo: < 3 segundos hasta 'Jarvis listo'
- [ ] Progress indicator vocal durante startup: 'Cargando modelos de voz... listo'
- [ ] Lazy loading para modelos opcionales (Edge TTS, Kokoro)
- [ ] Detectar si modelo necesita descarga y avisar por voz

## Definition of Done
- Cold start < 3 segundos
- Primera respuesta no tiene latencia adicional por carga de modelo"

gh issue create --repo $REPO \
  --title "[EPIC-23] Groq fast-path for classification and simple responses" \
  --label "epic:latency,priority:high" \
  --body "## Objetivo
Usar Groq (llama-3.3-70b, ~300ms latencia) para casos donde Claude API (~1s) es overkill.

## Routing rules
\`\`\`
Simple task (classify, summarize short) → Groq (~300ms)
Complex reasoning / code gen            → Claude API (~1s+)
Ultra-simple (known command)            → Local registry (0ms)
\`\`\`

## Tasks
- [ ] Adaptar \`groq_summarizer.py\` para routing inteligente basado en complejidad
- [ ] Classifier de complejidad: simple / medium / complex
- [ ] Tool result summarization → siempre Groq (no necesita razonamiento)
- [ ] Fallback: si Groq falla o rate limit → Claude API
- [ ] A/B test: calidad de respuesta Groq vs Claude para cada categoría

## Definition of Done
- Tool results siempre summarizados con Groq
- Latencia de summarization < 400ms"

# ── EPIC 5: Intelligence ───────────────────────────────────────────────────

gh issue create --repo $REPO \
  --title "[EPIC-24] Code context awareness — track project state in real-time" \
  --label "epic:intelligence,priority:high" \
  --body "## Objetivo
Jarvis debe saber en todo momento en qué archivo, función y proyecto estás trabajando.

## Context object
\`\`\`python
@dataclass
class CodeContext:
    project_root: Path
    language: str          # Python, TypeScript, Go, Rust, etc.
    framework: str         # FastAPI, React, Express, etc.
    current_file: Optional[Path]
    current_function: Optional[str]
    git_branch: str
    modified_files: list[Path]
    recent_errors: list[str]
    last_test_result: Optional[TestResult]
\`\`\`

## Tasks
- [ ] \`core/context/code_context.py\` — detección automática
- [ ] Watch de filesystem: detectar qué archivo está siendo editado (fsevents en macOS)
- [ ] Integración con git: branch, modified files, last commit en tiempo real
- [ ] Contexto inyectado en cada prompt a Claude (sin que el usuario lo pida)
- [ ] 'jarvis, en qué función estoy?' → respuesta sin API call si hay LSP
- [ ] Auto-detectar lenguaje y framework del proyecto

## Definition of Done
- Claude siempre recibe el contexto del proyecto actual
- 'en qué archivo estamos' se responde sin API call"

gh issue create --repo $REPO \
  --title "[EPIC-25] Smart output summarization — coding-specific templates" \
  --label "epic:intelligence,priority:high" \
  --body "## Objetivo
Summarizer especializado para cada tipo de output de coding. Nunca raw code en TTS.

## Tipos y templates
| Tipo | Template vocal |
|------|---------------|
| Error | 'Hay un {ErrorType} en línea {N} de {file}. El problema es {causa}' |
| Tests | 'Pasaron {N} de {total} tests. Los que fallaron son: {list}' |
| Build | 'Build exitoso en {time}. Bundle: {size}' |
| Git log | 'Los últimos {N} commits: {summary}' |
| Diff | 'Modificaste {N} archivos. Los cambios principales son: {summary}' |
| Stack trace | 'La excepción ocurrió en {function} ({file}:{line})' |

## Tasks
- [ ] \`core/summarizers/coding_summarizer.py\`
- [ ] Detectar tipo de output automáticamente
- [ ] Template por tipo con info mínima y relevante
- [ ] NUNCA leer stack traces completos — extraer línea relevante
- [ ] NUNCA leer código — siempre explicar en lenguaje natural

## Definition of Done
- Cualquier output de coding resumido en < 3 oraciones
- Sin raw code, sin stack traces completas en TTS"

gh issue create --repo $REPO \
  --title "[EPIC-26] Error pattern detection and proactive voice alert" \
  --label "epic:intelligence,priority:medium" \
  --body "## Objetivo
Detectar errores en el output de tools y alertar proactivamente sin que el usuario pregunte.

## Clasificación de severidad
\`\`\`
WARNING  → mencionar al final: 'Por cierto, hubo un warning en...'
ERROR    → interrumpir y explicar: 'Hay un error. {explicación}'
CRITICAL → pedir atención inmediata: 'STOP. Esto falló de forma crítica'
\`\`\`

## Tasks
- [ ] Watcher de output: detectar patterns (stderr, exit codes != 0, 'Error:', 'Exception:')
- [ ] Alert vocal sin esperar que el usuario pregunte
- [ ] Clasificar severidad automáticamente
- [ ] Sugerir fix conocido cuando el error matchea un pattern conocido
- [ ] 'jarvis, ignorá los warnings' → modo quiet para warnings

## Definition of Done
- Errores detectados y narrados en < 500ms de aparecer en el output
- Sugerencias de fix para errores comunes"

gh issue create --repo $REPO \
  --title "[EPIC-27] Test result narrator — voice-friendly test output" \
  --label "epic:intelligence,priority:medium" \
  --body "## Objetivo
Transformar output de test runners en resúmenes vocales concisos.

## Ejemplo
\`\`\`
Usuario: 'corré los tests'
Jarvis: 'Corrí 50 tests en 3.2 segundos. Pasaron 48, fallaron 2.
         El primer fallo está en UserService, test de login:
         esperaba status 200 pero recibió 401.
         ¿Querés que lo analice?'
\`\`\`

## Soportar frameworks
- JavaScript: Jest, Vitest, Mocha
- Python: pytest, unittest
- Go: go test
- Rust: cargo test

## Tasks
- [ ] Parsers por framework para extraer: total, passed, failed, time
- [ ] Para failures: test name + error message (SIN stack trace)
- [ ] 'revisá el primer error' → FileReadTool + análisis de la línea fallida
- [ ] Soporte para test watch mode: narrar solo cuando hay cambios en resultados

## Definition of Done
- Test results narrados en < 3 oraciones
- Failures explicados sin stack trace completa"

# ── EPIC 6: Advanced ──────────────────────────────────────────────────────

gh issue create --repo $REPO \
  --title "[EPIC-28] Multi-agent voice orchestration" \
  --label "epic:advanced,priority:medium" \
  --body "## Objetivo
Lanzar múltiples sub-agentes en paralelo vía voz.

## Ejemplo
\`\`\`
Usuario: 'mientras escribís los tests, buscá si hay una librería mejor para esto'
Jarvis: 'Arrancando dos agentes. El primero escribe tests, el segundo investiga librerías.'
[... tiempo después ...]
Jarvis: 'El agente de tests terminó. El de investigación todavía trabaja...'
\`\`\`

## Tasks
- [ ] \`core/agents/\` — sub-agent spawning con asyncio
- [ ] Cada agente tiene su propio tool context y conversación
- [ ] Orquestador vocal: reporta progreso de múltiples agentes
- [ ] Cancelación por voz de agentes individuales: 'cancelá el agente de tests'
- [ ] Resultados narrados en orden de finalización

## Definition of Done
- Dos agentes paralelos lanzados y monitoreados por voz
- Cancelación individual funciona"

gh issue create --repo $REPO \
  --title "[EPIC-29] MCP server integration via voice" \
  --label "epic:advanced,priority:medium" \
  --body "## Objetivo
Conectar MCP servers como extensiones de los tools de Jarvis, activables por voz.

## Ejemplo
\`\`\`
Usuario: 'mostrá los tickets del sprint en Linear'
Usuario: 'cerrá el ticket LIN-123 como done'
Usuario: 'conectate al servidor de Postgres y mostrá los usuarios activos'
\`\`\`

## Tasks
- [ ] \`core/mcp/\` — MCP client (Python MCP SDK)
- [ ] Config de MCP servers en \`~/.jarvis/mcp.yaml\`
- [ ] Auto-discovery de tools disponibles en cada server
- [ ] Voice triggers para MCP tools (auto-generados desde la descripción del tool)
- [ ] Jarvis como MCP server: exponer tools a Claude Code CLI

## Definition of Done
- MCP server configurado en YAML disponible por voz
- Tool discovery automático"

gh issue create --repo $REPO \
  --title "[EPIC-30] Session memory and resume — cross-session context" \
  --label "epic:advanced,priority:medium" \
  --body "## Objetivo
Jarvis recuerda lo que hiciste en sesiones anteriores.

## Ejemplo
\`\`\`
Usuario: 'jarvis, ¿qué estábamos haciendo ayer?'
Jarvis: 'Estabas implementando autenticación JWT. Terminaste el middleware
         pero te faltaba el refresh token endpoint. ¿Seguimos?'
\`\`\`

## Tasks
- [ ] \`core/memory/\` — persistencia de sesión en \`~/.jarvis/sessions/\`
- [ ] Session summary al cerrar: qué se hizo, qué falta, archivos modificados
- [ ] Resume: 'jarvis, continuá donde estábamos'
- [ ] Memory search por voz: 'cómo resolvimos el problema de CORS la semana pasada'
- [ ] Integración con Engram si está disponible
- [ ] Limpieza automática de sesiones viejas (> 30 días)

## Definition of Done
- 'qué hicimos ayer' retorna contexto de la sesión anterior
- Resume arranca exactamente donde se quedó"

gh issue create --repo $REPO \
  --title "[EPIC-31] LSP integration — code intelligence via voice" \
  --label "epic:advanced,priority:low" \
  --body "## Objetivo
Language Server Protocol para code intelligence sin necesitar abrir un editor.

## Ejemplos de uso
\`\`\`
'andá a la definición de authenticate'
'dónde se usa la función createUser'
'qué parámetros acepta esta función'
\`\`\`

## Tasks
- [ ] \`core/lsp/\` — LSP client (python-lsp-jsonrpc o similar)
- [ ] Go-to-definition por voz → abre archivo en \$EDITOR
- [ ] Find references → narra los top 3 lugares donde se usa
- [ ] Hover info → narra la signature y docstring de la función
- [ ] Auto-detectar LSP server según lenguaje (pylsp, typescript-language-server, etc.)
- [ ] Fallback: si no hay LSP → ripgrep para find references

## Definition of Done
- Go-to-definition funciona por voz
- Find references narra los resultados"

gh issue create --repo $REPO \
  --title "[EPIC-32] Claude Code CLI as PTY backend (hybrid mode)" \
  --label "epic:advanced,priority:low" \
  --body "## Objetivo
Modo híbrido donde Jarvis wrappea el Claude Code CLI para máxima compatibilidad, con control por voz.

## Use case
Usuario que quiere la experiencia completa de Claude Code + control 100% por voz.

## Tasks
- [ ] PTY adapter para Claude Code CLI (adaptar el existente de Gemini CLI)
- [ ] Patch del lexer para el output format de Claude Code (distinto a Gemini)
- [ ] Tool calls de Claude Code interceptados y anunciados por voz
- [ ] Permission prompts de Claude Code → voice approval gate
- [ ] Modo de selección: \`jarvis --mode pty --cli claude-code\`
- [ ] Detectar instalación de Claude Code CLI en el sistema

## Definition of Done
- Claude Code CLI wrapeado y controlado 100% por voz
- Permission prompts resueltos por voz sin tocar el teclado"

echo ""
echo "✅ Todas las issues creadas en https://github.com/$REPO/issues"
echo "📋 Próximo paso: asignar issues a milestones en GitHub"
