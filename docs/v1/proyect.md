# 🎙️ Gemini Voice CLI Extension (Codename: J.A.R.V.I.S.)

## 📝 Descripción General
**J.A.R.V.I.S.** es una extensión de interfaz de voz (Voice-First) diseñada para actuar como intermediario inteligente para la CLI de Gemini. Su objetivo principal es resolver el problema de la sobrecarga de información cuando los LLMs en terminales generan enormes bloques de texto o código, permitiendo a los desarrolladores mantener su flujo de trabajo mediante un control "manos libres" y resúmenes conversacionales.

## 🎯 Problema que Resuelve
Los sistemas tradicionales de Text-to-Speech (TTS) fallan al intentar leer código fuente o respuestas largas de forma literal. Esta herramienta intercepta esas salidas complejas, las procesa para generar un resumen conversacional (ej. *"He generado el script de Python, ¿quieres que lo ejecute o lo guarde?"* en lugar de dictar el código línea por línea) y permite al usuario aceptar, rechazar o modificar acciones usando comandos de voz.

## ✨ Características Principales

1. **Traductor Inteligente (Intelligent Summarization):** 
   - Evita la lectura de bloques de código crudos.
   - Pasa los outputs de Gemini por un "prompt de resumen" antes de enviarlos al motor de voz para hacerlos conversacionales.
2. **Motor Híbrido de Voz (I/O):**
   - **STT (Speech-to-Text):** Soporte intercambiable entre proveedores locales (ej. `faster-whisper`) y remotos (ej. OpenAI Whisper API).
   - **TTS (Text-to-Speech):** Soporte intercambiable entre proveedores locales (ej. Piper) y remotos (ej. ElevenLabs).
   - Cambio de modo (Local/Remoto) mediante variables de entorno o configuración, sin alterar la lógica de negocio.
3. **Barge-in e Interrupción (VAD):**
   - Detección de Actividad de Voz (VAD) de baja latencia monitoreando el micrófono constantemente.
   - Permite al usuario interrumpir al asistente mientras está hablando. Al detectar la voz del usuario, el sistema detiene inmediatamente el audio (TTS) y vuelve al estado de escucha (`LISTENING`).
4. **Control de Flujo de Trabajo por Voz:**
   - Reconocimiento de intenciones explícitas (confirmación, rechazo, explicación).
   - Pausa automática de acciones destructivas (escribir archivos, ejecutar comandos de shell) hasta obtener la aprobación verbal del usuario.

## 🏗️ Arquitectura y Stack Tecnológico

El proyecto está diseñado bajo una **Arquitectura Hexagonal (Puertos y Adaptadores)** para evitar el acoplamiento con librerías de IA o audio específicas.

- **Lenguaje Principal:** Python 3.10+
- **Core System (El Cerebro):** Controlado por una Máquina de Estados Finita (FSM) con estados como `IDLE`, `LISTENING`, `THINKING`, `SUMMARIZING`, `SPEAKING` y `WAITING_APPROVAL`.
- **Manejo de Concurrencia (Threading):** Hilos separados para la FSM/UI, la salida de audio (interrumpible) y la escucha del micrófono.
- **Tecnologías Clave:**
  - **Audio I/O:** `pyaudio` / `sounddevice`.
  - **VAD:** `silero-vad` o `webrtcvad`.
  - **STT/TTS:** `faster-whisper`, `piper-tts`, APIs de OpenAI y ElevenLabs.
  - **LLM:** Google Generative AI API (Gemini).

## 📁 Estructura del Proyecto

El código está organizado modularmente para separar la lógica de negocio de las integraciones externas:

- `/core`: Lógica principal, Máquina de Estados (FSM) y orquestación.
- `/adapters`: Implementaciones de los puertos (Strategy Pattern) para STT, TTS y LLM.
- `/audio`: Módulos de grabación con VAD y reproductores de audio interrumpibles.
- `main.py`: Punto de entrada de la aplicación.