# Reporte de Revisión Técnica: Proyecto J.A.R.V.I.S. (Gemini Voice CLI)

Este documento detalla los hallazgos de la auditoría técnica realizada al código base. Se categorizan por seguridad, arquitectura, deuda técnica y experiencia de usuario (UX).

---

## 1. Riesgos de Seguridad Críticos (Prioridad: ALTA)

### 1.1. Inyección de Comandos vía Voz (Riesgo de Ejecución Remota/Local)
- **Falla:** El componente `GhostTyper.type_string` toma cualquier texto transcrito por el motor de STT y lo "tipea" directamente en la terminal activa, seguido de un comando `Return` (Enter).
- **Impacto:** Si el STT interpreta erróneamente ruido de fondo o si un atacante físico/remoto (vía audio) dicta un comando como `"rm -rf /"`, el sistema lo ejecutará sin confirmación humana.
- **Recomendación:** Implementar una capa de **confirmación obligatoria** para comandos que no sean de navegación simple. Usar un LLM para clasificar la intención (Intents) antes de inyectar en la terminal.

### 1.2. Uso Inseguro de `subprocess` con `shell=True`
- **Falla:** En `adapters/stt/ghost_typer.py`, se utiliza `subprocess.run(f"echo -n '{safe_text}' | pbcopy", shell=True)`. 
- **Impacto:** Aunque se intenta escapar las comillas, el uso de `shell=True` con entrada de texto externa (transcripción de voz) es una vulnerabilidad clásica de inyección de shell.
- **Recomendación:** Evitar `shell=True`. Usar el argumento `input` de `subprocess.run` y pasar los argumentos como una lista: `subprocess.run(["pbcopy"], input=text.encode('utf-8'))`.

### 1.3. Servidor TCP sin Autenticación
- **Falla:** El `jarvis_daemon.py` levanta un servidor en el puerto `49999` que acepta cualquier conexión local y procesa el texto recibido como entrada para el "cerebro".
- **Impacto:** Cualquier proceso malicioso corriendo localmente puede inyectar notificaciones falsas o forzar al sistema a hablar/procesar datos, agotando la cuota de la API de Gemini.
- **Recomendación:** Implementar un handshake básico o un token de seguridad compartido entre el hook y el daemon.

---

## 2. Arquitectura y Concurrencia (Prioridad: MEDIA)

### 2.1. Bloqueo del Bucle de Eventos (Asyncio + Threads)
- **Falla:** El método `MacSayTTS.speak` realiza un bucle `while` bloqueante que monitorea el proceso `say`. Al ser llamado desde el hilo de `asyncio` (en `main.py`), congela el procesamiento de nuevos tokens hasta que termina de hablar.
- **Impacto:** Latencia acumulada. Si Gemini genera mucho texto, el Lexer no puede procesar el siguiente chunk mientras el anterior se está reproduciendo.
- **Recomendación:** Convertir `speak` en una función verdaderamente asíncrona (`async def`) usando `asyncio.create_subprocess_exec`.

### 2.2. Fragmentación de Lógica (Main vs Daemon)
- **Falla:** Existen dos puntos de entrada con lógicas similares pero divergentes: `main.py` (intercepción vía PTY) y `jarvis_daemon.py` (servidor de red).
- **Impacto:** Duplicidad de código y dificultad para mantener una única "fuente de verdad" para el estado del asistente.
- **Recomendación:** Unificar en una arquitectura de servicio donde el PTY sea un cliente más que le habla al Daemon, o eliminar el Daemon si la intercepción vía PTY es suficiente.

### 2.3. Limpieza de TUI Frágil
- **Falla:** `clean_and_filter_chunk` depende de una lista negra (`TUI_BLACKLIST`) y regex manuales para limpiar caracteres ANSI y cajas de texto.
- **Impacto:** Si la CLI de Gemini actualiza su diseño visual, el asistente empezará a leer "basura" visual o dejará de leer información importante.
- **Recomendación:** Utilizar un parser de terminal virtual (como `pyte`) para extraer solo el texto plano de la pantalla de forma robusta.

---

## 3. Deuda Técnica y Portabilidad (Prioridad: BAJA)

### 3.1. Dependencia Absoluta de macOS
- **Hallazgo:** El proyecto depende de `osascript` (AppleScript), `pbcopy`, `say` y `afplay`. No funcionará en Linux o Windows sin cambios mayores.
- **Recomendación:** Abstraer estos comandos en los Adaptadores y proveer alternativas (ej. `xclip` para Linux, `espeak` o `piper` para TTS multiplataforma).

### 3.2. Secuestro del Portapapeles (UX)
- **Hallazgo:** `GhostTyper` utiliza el portapapeles del sistema para inyectar texto.
- **Impacto:** Borra lo que el usuario tenga copiado, lo cual es extremadamente intrusivo.
- **Recomendación:** Usar inyección directa de caracteres vía AppleScript (`keystroke`) o investigar métodos de inyección de PTY que no dependan de la UI.

### 3.3. Manejo de Errores Silencioso
- **Hallazgo:** Múltiples bloques `try...except Exception: pass` en el código (especialmente en `vad_listener.py` y `hooks/notification.py`).
- **Impacto:** Errores críticos (como fallos de permisos o desconexión de micro) pasan desapercibidos, dificultando el debugging.
- **Recomendación:** Loguear siempre el error y, si es crítico, notificar al usuario vía TTS ("Señor, he perdido la conexión con el micrófono").

---

## 4. Oportunidades de Mejora (Roadmap)

1. **Estado Centralizado:** Implementar la FSM (Máquina de Estados) real mencionada en el `TECHNICAL_SPEC.md` para coordinar `IDLE`, `THINKING`, `SPEAKING` de forma global.
2. **Mejora de Latencia:** Reemplazar `mac_say_tts` por un motor local como **Piper** (vía ONNX) para una voz más natural y con mejor control de stream.
3. **Context Awareness:** Pasar al `GeminiSummarizer` no solo el chunk actual, sino los últimos 2-3 para que el resumen tenga contexto de lo que se habló antes.
4. **Seguridad:** Implementar un modo "Solo Lectura" donde J.A.R.V.I.S. solo hable pero no tenga permisos para tipear en la terminal sin que el usuario presione una tecla física.
