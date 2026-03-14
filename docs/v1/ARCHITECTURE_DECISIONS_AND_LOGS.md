# Bitácora de Desarrollo y Decisiones de Arquitectura (J.A.R.V.I.S.)

Acá dejamos constancia de la sangre derramada para que el día de mañana, cuando otro guacho mire el repositorio, entienda por qué tomamos las decisiones que tomamos. Un arquitecto no solo tira código, documenta el dolor.

## Fase 1: Motor de Audio Híbrido y Barge-in (Completada)

### El Objetivo
Validar que podemos tener un hilo reproduciendo audio y otro hilo escuchando el micrófono al mismo tiempo, logrando que si el usuario habla (barge-in), el sistema se calle instantáneamente (latencia < 200ms).

### Decisión Arquitectónica Clave
**Rechazo absoluto de Docker.** El usuario propuso dockerizar el entorno para procesar audio en tiempo real en macOS. Se rechazó de plano porque la capa de virtualización de Hypervisor (que rutea CoreAudio a ALSA/PulseAudio de Linux) introduce una latencia inaceptable que enmascara los problemas de concurrencia y bloqueos de hilos (Deadlocks) de la prueba. El desarrollo de I/O de bajo nivel se hace **NATIVO**.

### Problemas Encontrados y Soluciones
1. **Binding de C en macOS (PortAudio):**
   - *Problema:* `pyaudio` crashea al instalar porque no encuentra los headers de C.
   - *Solución:* Instalar `portaudio` vía Homebrew y pasar las banderas del compilador explícitamente a `pip`: `env LDFLAGS="-L$(brew --prefix portaudio)/lib" CFLAGS="-I$(brew --prefix portaudio)/include" pip install pyaudio`.

2. **La trampa de Python 3.14 (Alpha) y `webrtcvad`:**
   - *Problema:* El usuario estaba corriendo una versión alpha/nightly de Python (3.14) que elimina el paquete `pkg_resources` (parte de `setuptools` v70+) por defecto. La librería `webrtcvad` (que es vieja pero roca sólida en C) depende de `pkg_resources` para ubicar sus binarios, lo que resultó en un `ModuleNotFoundError`.
   - *Solución:* Forzar un downgrade de `setuptools` a una versión clásica (v69) dentro del entorno virtual con `pip install "setuptools<70"`. 

### Resultado
La prueba de concurrencia (`poc_barge_in.py`) usando `threading.Event` y `webrtcvad` funcionó a la perfección. La interrupción del "habla" simulada fue instantánea al detectar voz.

---

## Fase 2: Lexer en Tiempo Real / Smart Chunking (En Progreso)

### El Problema
Gemini CLI devuelve los datos por streaming (token a token). No podemos mandar cada token suelto al TTS (voz robótica), y si le mandamos el código en crudo, lee "import coma react...". Necesitamos parsear Markdown al vuelo.

### La Solución Diseñada
Una Máquina de Estados Finita (Lexer) que se interpone en el Stream:
- Acumula tokens normales y los "escupe" al detectar puntuación (`.`, `?`, `\n`) para enviarlos a voz (baja latencia).
- Si detecta un bloque de código (`` ``` ``), bloquea la salida, acumula TODO el código de forma silenciosa, y recién lo suelta entero cuando detecta el cierre (`` ``` ``) para enviarlo a la IA Resumidora.

### Resultado Fase 2
El lexer funciona detectando los límites de los bloques de código y las puntuaciones. Simuló la ingesta de un stream asíncrono palabra por palabra. El buffering es estable y previene que el TTS reciba fragmentos rotos o crudos de código.

## Fase 3: Integración LLM (El Traductor) y TTS

### Decisiones Arquitectónicas
1. **TTS (Text-to-Speech):** Se decidió utilizar el comando nativo `say` de macOS.
   - *Por qué:* Latencia cero, sin dependencias de red. Es rústico pero ideal para validar la lógica de la Máquina de Estados (Lexer) -> Audio.
   - *Manejo de Interrupción:* Al usar `subprocess.Popen` para invocar a `say`, podemos monitorear un `threading.Event` (nuestra señal de Barge-in del VAD) y matar el proceso (`.terminate()`) instantáneamente si el usuario habla.

2. **LLM (El Traductor/Summarizer):** Se utiliza `gemini-1.5-flash` vía la librería `google-generativeai`.
   - *Por qué:* Necesitamos velocidad pura. Si usamos un modelo pesado para resumir un bloque de código, la latencia arruinará la experiencia. El modelo Flash con un system prompt estricto es la herramienta adecuada.

### Resultado Fase 3
Integración exitosa entre el Lexer, Gemini Flash (Summarizer) y el TTS de macOS (`say`). El flujo asíncrono no se bloquea y el comando `say` permite interrupción vía proceso (Popen.terminate). Arquitectura acoplada mediante eventos validada.

## Fase 4: CLI Hooking y Pseudo-Terminales (PTY)

### Desafío Superado
Se logró 'secuestrar' una CLI moderna (`gemini`) engañándola para que crea que se ejecuta en una terminal real. Esto previene que la CLI cambie su comportamiento de buffering o deshabilite colores.

### Problemas de Arquitectura Resueltos:
1. **Deadlock de I/O:** Inicialmente, bloquear la lectura de la CLI dejaba al usuario sin teclado. *Solución:* Implementación de multiplexación de I/O con `select.select` vigilando simultáneamente `sys.stdin` (teclado real) y el File Descriptor del PTY.
2. **Ventana Colapsada (80x24):** Las CLIs dibujaban sus interfaces rotas porque el PTY por defecto asume el tamaño de consola más antiguo. *Solución:* Estrategia de doble cañón: inyectar variables de entorno (`COLUMNS`, `LINES`) antes del fork, y forzar el kernel usando `fcntl.ioctl` con la estructura C exacta (empaquetada vía `struct`).

## Fase 5: Orchestrator Principal

### Arquitectura del Main Loop
- **Hilo 1 (Main):** Bucle de multiplexación I/O (`select`). Mantiene la latencia del teclado y la pintura de la terminal en 0ms. Limpia códigos ANSI vía Regex (`[...`) y encola el texto limpio.
- **Hilo 2 (Brain):** Bucle de eventos `asyncio` dedicado. Desencola el texto, lo pasa por el `StreamingLexer` y ejecuta el LLM (Gemini) o TTS (`say`) sin bloquear la UI.
- **Hilo 3 (VAD):** Hilo demonio con WebRTCVAD monitoreando el micro. Dispara un `threading.Event` si el usuario habla o tipea. Este evento es leído por el TTS para frenar de inmediato.

## El Problema del TUI Chrome (Fase Final)

### Problema
La CLI de Gemini dibuja cajas de Markdown y menús interactivos usando caracteres de dibujo de cajas (`▀, ▄, ─`) y cambia el título de la ventana (`]0;...`). El limpiador ANSI normal no atrapaba esto, lo que causaba que el Lexer recibiera pedazos de UI destrozada en lugar de las oraciones de la IA.

### Solución
Implementar Regex múltiples en el Orquestador:
1. Limpiador ANSI estándar.
2. Limpiador de *Box Drawings* de Unicode (bloques y líneas de Markdown).
3. Limpiador de Window Titles (`]0;`).
4. Lista negra explícita de UI (`UI_CHROME`) para ignorar barras de estado y hotkeys de la interfaz.

### Bug Fix: Regex Destructivo de Espacios
- *Problema:* El Lexer estaba recibiendo oraciones sin espacios (ej: `¡Holamundo!`), lo que causaba que deletreara al reproducir.
- *Causa:* La regex `BOX_DRAWING_CLEANER` incluía por error un espacio literal (` `) en la lista de caracteres a eliminar, lo que borraba todos los espacios de las respuestas.
- *Solución:* Remover el espacio de la clase de caracteres regex.

## Fase 6: El Pivot Arquitectónico - De PTY Wrapper a CLI Hooks

### El Fracaso del PTY/TUI Scraping
Intentar envolver la CLI de Gemini en un Pseudo-Terminal (PTY) y parsear el `stdout` resultó ser una negrada insostenible. Aunque logramos limpiar los códigos ANSI básicos y los caracteres de dibujo de cajas, la interfaz TUI (Text User Interface) ensucia el output de maneras impredecibles (movimientos de cursor, repintado de pantalla, eco de teclado local). Esto rompe nuestro Lexer porque los pedazos de texto llegan fragmentados, fuera de orden o mezclados con basura de la UI. Construir sobre esta base es de tutorial de YouTube, no de ingeniería seria.

### La Nueva Solución: Gemini CLI Hooks
Descubrimos (leyendo la documentación oficial) que la Gemini CLI soporta **Hooks** de ciclo de vida (específicamente `AfterModel`). Esto nos permite interceptar la respuesta de la IA de forma limpia y estructurada (vía JSON por `stdin`/`stdout`) *antes* de que la CLI intente renderizar la TUI.

### Próximos Pasos (Lo que necesitamos)
1. **Deprecar el Wrapper:** Eliminar la lógica de `pty_wrapper.py` y el orquestador viejo.
2. **Definir el Contrato (JSON Schema):** **URGENTE**. Necesitamos el esquema JSON exacto que el hook `AfterModel` recibe por `stdin` y el formato exacto que debe devolver por `stdout`. Sin esto, estamos ciegos.
3. **Nuevo Entrypoint:** Crear un script (`hook_after_model.py`) que respete este contrato de I/O, procese el texto limpio a través de nuestro pipeline existente (Lexer -> Flash Summarizer -> TTS) y devuelva el control a la CLI gracefully.
