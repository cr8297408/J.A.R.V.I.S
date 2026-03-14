# Arquitectura de Integración CLI (Hooking Strategy)
**Estado:** Draft Inicial
**Objetivo:** Definir cómo `J.A.R.V.I.S.` se inyecta entre el usuario y una CLI subyacente (Gemini CLI, OpenCode, etc.) sin modificar el código fuente original de la CLI.

## El Desafío del CLI Wrapper
No podemos modificar el código de `gemini-cli` ni de `opencode`. Tenemos que envolver su ejecución (wrapper) y comportarnos como un "Man-in-the-Middle" (MitM) de las tuberías estándar (Standard Streams).

### 1. Intercepción de Tuberías (Standard Streams)
El orquestador en Python (`J.A.R.V.I.S.`) debe lanzar el proceso de la CLI objetivo usando el módulo `subprocess` o `pty` (pseudo-terminal) de Python.

- **`stdin` (Entrada):** J.A.R.V.I.S. escucha al usuario (micrófono -> STT -> Texto) y *escribe* ese texto en el `stdin` del proceso de la CLI, simulando que el usuario lo tecleó y presionó Enter.
- **`stdout` / `stderr` (Salida):** J.A.R.V.I.S. *lee* en tiempo real lo que la CLI escupe. En lugar de imprimirlo directamente en la pantalla, lo intercepta, lo pasa por el Módulo de Resumen (LLM intermediario), y luego lo reproduce por voz (TTS) y lo imprime formateado en la terminal.

### 2. Pseudo-Terminales (PTY) vs Subprocess
Usar `subprocess.Popen(..., stdout=PIPE, stdin=PIPE)` es lo más fácil, pero muchas CLIs modernas (como las que tienen spinners, colores ANSI o menús interactivos) detectan que no están corriendo en una terminal real (TTY) y cambian su comportamiento o crashean.

**Decisión Arquitectónica Clave:**
Para soportar herramientas avanzadas como OpenCode en el futuro, es obligatorio usar **`pty` (pseudo-terminals)** en sistemas Unix (Linux/macOS) o librerías multiplataforma como `pexpect`. Esto engaña a la CLI subyacente haciéndole creer que está interactuando con una terminal real.

### 3. Parseo de Trama (Chunking)
Gemini CLI no devuelve toda la respuesta de golpe; la va "stremeando" (token a token o línea a línea).
J.A.R.V.I.S. tiene que acumular un "chunk" lógico (ej: hasta que detecta un punto final, un salto de línea doble, o el fin de un bloque de código) antes de enviarlo al resumidor y al TTS. Si mandás a leer palabra por palabra, la latencia te arruina.

### 4. Capa de Adaptadores CLI (Strategy Pattern)
Así como hicimos con el Audio, la CLI objetivo debe ser intercambiable.

- **Interface `ICLIWrapper`:**
  - `start_session()`
  - `send_input(text: str)`
  - `read_output_stream() -> AsyncGenerator[str, None]`
  - `kill()`

- **Adaptadores:**
  - `GeminiCLIAdapter`: Entiende los delimitadores específicos o el formato de salida de Gemini CLI.
  - `OpenCodeAdapter`: (Futuro) Entenderá cuándo OpenCode está pidiendo permisos de ejecución o modificando el file system.

## Resumen del Flujo de Datos (Data Flow)

1. **Usuario:** (Micrófono) "Creá un archivo index.js con un console.log"
2. **J.A.R.V.I.S. (STT):** Transcribe el audio.
3. **J.A.R.V.I.S. (Orchestrator):** Inyecta el texto -> `GeminiCLIAdapter.send_input()`
4. **Proceso Oculto (gemini-cli):** Procesa y escupe por `stdout`: "Claro, aquí tienes el código:\n```javascript\nconsole.log('Hola');\n```"
5. **J.A.R.V.I.S. (Interceptor):** Captura el bloque. Llama al LLM de resumen.
6. **J.A.R.V.I.S. (Summarizer):** Devuelve: "Listo, armé el archivo index.js. ¿Querés que lo guarde?"
7. **J.A.R.V.I.S. (TTS):** Habla el resumen mientras monitorea el VAD por si lo interrumpen.
8. **Usuario:** (Micrófono) "Sí, mandale". (Vuelve al paso 1).
