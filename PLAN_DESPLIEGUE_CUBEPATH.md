# Plan de Despliegue: J.A.R.V.I.S. Interactive Web Demo (Cubepath)

Este documento detalla la estrategia para migrar el prototipo local de J.A.R.V.I.S. (basado en macOS) a una arquitectura basada en la nube desplegable en un servidor de **Cubepath**, permitiendo una demo web interactiva con voz y logs en tiempo real.

---

## 1. Visión General del Sistema
El objetivo es permitir que cualquier usuario entre a una URL, vea la terminal de Gemini CLI en su navegador, hable a través de su micrófono y reciba respuestas de voz de J.A.R.V.I.S., mientras observa los procesos internos del "cerebro" en un panel de logs lateral.

### Flujo de Datos
1.  **Entrada de Voz:** Navegador (Web Audio API) -> WebSocket -> Servidor (STT).
2.  **Procesamiento:** Transcripción -> Inyección en PTY (Linux) -> Gemini CLI.
3.  **Salida de Texto:** Gemini CLI -> PTY -> WebSocket -> Navegador (xterm.js).
4.  **Salida de Voz:** Respuesta Gemini -> Summarizer -> TTS (EdgeTTS) -> Navegador (Audio Stream).
5.  **Logs:** Eventos del sistema -> Custom Log Handler -> WebSocket -> Navegador (Log Panel).

---

## 2. Arquitectura de Backend (Python / FastAPI)
Se creará un nuevo punto de entrada `core/server/jarvis_web_api.py`.

### A. WebSocket Hub
Manejará una conexión bidireccional multiplexada para:
-   **Terminal:** Stream de entrada/salida ANSI.
-   **Audio:** Stream binario de audio (PCM/Opus).
-   **Logs:** JSON con eventos de estado (`thinking`, `transcribing`, `speaking`).

### B. Adaptadores Linux-Compatibles
Dado que Cubepath corre sobre Linux (Ubuntu/Debian), eliminaremos las dependencias de macOS:
-   **STT:** Cambio de `mlx_stt` (Apple Silicon) a `OpenAI Whisper API` o `Groq Whisper` para latencia ultra-baja.
-   **TTS:** Uso de `EdgeTTS` (ya integrado), que funciona perfectamente en Linux sin drivers de audio locales.
-   **PTY:** El `PtyCLIWrapper` actual es compatible con Linux (`pty.fork()`), pero se optimizará para manejar múltiples sesiones.

### C. Log Streamer
Implementación de un `logging.Handler` que capture todos los logs de `jarvis_daemon.log` y los emita vía WebSocket en tiempo real.

---

## 3. Arquitectura de Frontend (React / Vite)
Actualización de `apps/jarvis-landing` para incluir la consola interactiva.

### A. Terminal Web (xterm.js)
Integración de una terminal real en el navegador que renderice la salida de Gemini CLI con soporte completo para colores y formatos ANSI.

### B. Captura de Audio y Reproducción
-   Uso de `MediaRecorder` para capturar fragmentos de voz del usuario.
-   VAD (Voice Activity Detection) en el lado del cliente para reducir el tráfico de red.
-   Reproductor de audio dinámico para las respuestas de J.A.R.V.I.S.

### C. Dashboard de Logs
Un panel lateral con scroll automático que muestre:
-   Razonamiento del LLM (Summarizer).
-   Estado de los hooks de Gemini.
-   Detección de intenciones.

---

## 4. Estrategia de Contenedores (Docker)
Para asegurar que el entorno sea idéntico en Cubepath, usaremos Docker.

### Dockerfile (Propuesta)
```dockerfile
FROM python:3.10-slim

# Instalar dependencias de sistema y Node.js (para gemini-cli)
RUN apt-get update && apt-get install -y \
    curl \
    gnupg \
    portaudio19-dev \
    gcc \
    python3-dev \
    && curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs \
    && rm -rf /var/lib/apt/lists/*

# Instalar Gemini CLI globalmente
RUN npm install -g @google/generative-ai-cli

# Configurar directorio de trabajo
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código del proyecto
COPY . .

# Exponer puertos (8000 para la Web API)
EXPOSE 8000

# Comando de inicio
CMD ["uvicorn", "core.server.jarvis_web_api:app", "--host", "0.0.0.0", "--port", "8000"]
```

---

## 5. Pasos para la Implementación (Milestones)

1.  **Fase 1: API Core (Backend)**
    -   Crear `core/server/jarvis_web_api.py`.
    -   Adaptar `PtyCLIWrapper` para no depender de `sys.stdin` (modo headless).
    -   Integrar STT remoto (Groq/OpenAI).

2.  **Fase 2: UI Interactiva (Frontend)**
    -   Instalar `xterm.js` en `jarvis-landing`.
    -   Implementar el bridge de WebSocket en React.
    -   Añadir visualizador de voz y panel de logs.

3.  **Fase 3: Dockerización y Cubepath**
    -   Crear `Dockerfile` y `docker-compose.yml`.
    -   Configurar variables de entorno (`GEMINI_API_KEY`, etc.).
    -   Desplegar en el servidor de Cubepath.

4.  **Fase 4: Validación**
    -   Pruebas de latencia en la transcripción.
    -   Verificación de la interrupción (Barge-in) vía WebSocket.
    -   Ajuste del CSS para mantener el estilo Apple Design System en la terminal.

---

**Preparado para iniciar la implementación de la Fase 1.**
