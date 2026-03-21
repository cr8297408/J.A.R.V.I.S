# Reporte de Errores y Bugs: Proyecto J.A.R.V.I.S.

Este documento consolida los fallos detectados, riesgos de seguridad y tareas técnicas pendientes identificadas durante la auditoría técnica y el desarrollo del proyecto.

---

## 1. Riesgos de Seguridad Críticos (Prioridad: ALTA)

- **[BUG-001] Inyección de Comandos vía Voz:** `GhostTyper.type_string` tipea cualquier transcripción del STT en la terminal activa sin confirmación. Riesgo de ejecución accidental o maliciosa de comandos (ej: `rm -rf /`).
- **[BUG-002] Inyección de Shell en `pbcopy`:** Uso de `shell=True` en `adapters/stt/ghost_typer.py` con texto externo. Vulnerabilidad de inyección de shell.
- **[BUG-003] Daemon TCP Vulnerable:** El servidor en el puerto `49999` no tiene autenticación, permitiendo inyección de datos desde cualquier proceso local.

## 2. Fallos de Arquitectura y Concurrencia (Prioridad: MEDIA)

- **[BUG-004] Bloqueo de Asyncio en TTS:** `MacSayTTS.speak` utiliza un bucle bloqueante que detiene el procesamiento de nuevos tokens de Gemini mientras se reproduce audio.
- **[BUG-005] Limpieza de TUI Frágil:** Dependencia de regex manuales (`TUI_BLACKLIST`) para limpiar caracteres ANSI, lo que puede causar lectura de "basura" visual si la CLI cambia su diseño.
- **[BUG-006] Fragmentación de Lógica:** Duplicidad de funciones entre `main.py` y `jarvis_daemon.py`, dificultando el mantenimiento de un estado único.

## 3. Deuda Técnica y Portabilidad (Prioridad: BAJA)

- **[BUG-007] Dependencia Exclusiva de macOS:** Uso de comandos específicos (`osascript`, `pbcopy`, `say`, `afplay`) que impiden el funcionamiento en Linux o Windows.
- **[BUG-008] Secuestro del Portapapeles:** `GhostTyper` sobrescribe el portapapeles del sistema para inyectar texto, degradando la experiencia de usuario (UX).
- **[BUG-009] Manejo de Errores Silencioso:** Múltiples bloques `try...except Exception: pass` que ocultan fallos críticos de permisos o hardware (especialmente en `vad_listener.py`).

## 4. Bugs de Regresión y Errores Históricos (Corregidos/Documentados)

- **[FIX-001] Regex Destructivo de Espacios:** La regex `BOX_DRAWING_CLEANER` eliminaba espacios literales de las respuestas. (Corregido).
- **[FIX-002] Incompatibilidad Python 3.14+:** Fallo de `webrtcvad` por eliminación de `pkg_resources`. Requiere versiones específicas de `setuptools`.

## 5. Errores Identificados en la Sesión Actual (Landing Page)

- **[BUG-010] Conflictos de Peer Dependencies:** Durante la instalación de la landing page en `apps/jarvis-landing/`, se detectaron conflictos de versiones entre dependencias de React y Vite. 
    - *Estado:* Mitigado temporalmente usando `--legacy-peer-deps`.
- **[BUG-011] Acceso Denegado a Logs:** El sistema de archivos ignora por defecto el archivo `dev_server.log`, dificultando el monitoreo automático de errores en tiempo real desde herramientas de diagnóstico estándar.

---

## 6. Decisiones y Tareas Pendientes

- **[TODO-001] Selección de Motor STT:** Decidir entre motor local (`mlx`) o API para producción definitiva.
- **[TODO-002] Implementación de FSM:** Crear la Máquina de Estados Finitos centralizada para coordinar `IDLE`, `THINKING` y `SPEAKING`.
- **[TODO-003] Confirmación de Comandos:** Implementar capa de validación vía LLM antes de ejecutar acciones en la terminal.

---
*Última actualización: 20 de marzo de 2026*
