# 🎙️ Gemini Voice CLI Extension (Codename: J.A.R.V.I.S.)

## 📝 Descripción General

**J.A.R.V.I.S.** es una extensión de interfaz de voz (Voice-First) diseñada para actuar como un intermediario inteligente para la CLI de Gemini. Su objetivo principal es optimizar el flujo de trabajo de los desarrolladores permitiendo un control "manos libres" y transformando las extensas salidas de texto o código de los LLM en resúmenes conversacionales digeribles.

## 🎯 El Problema que Resuelve

Los sistemas tradicionales de Text-to-Speech (TTS) fallan al intentar leer código fuente o respuestas largas de forma literal, lo que interrumpe la concentración del desarrollador. **J.A.R.V.I.S.** intercepta estas salidas, las procesa mediante un "traductor inteligente" para generar un resumen ejecutivo y permite al usuario interactuar con la CLI mediante comandos de voz naturales.

## ✨ Características Principales

### 1. Traductor Inteligente (Intelligent Summarization)
- Evita la lectura tediosa de bloques de código crudos.
- Procesa los outputs de Gemini a través de un prompt de resumen especializado antes de enviarlos al motor de voz.
- Ejemplo: *"He generado el script de Python solicitado. ¿Quieres que lo ejecute o prefieres que lo guarde en un archivo?"*

### 2. Motor Híbrido de Voz (I/O)
- **STT (Speech-to-Text):** Soporte intercambiable para proveedores locales (como `faster-whisper`) y remotos (como OpenAI Whisper API).
- **TTS (Text-to-Speech):** Compatibilidad con motores locales de baja latencia (como Piper) y servicios premium en la nube (como ElevenLabs).
- **Flexibilidad:** Cambio entre modo local y remoto mediante configuración, sin afectar la lógica de negocio.

### 3. Barge-in e Interrupción (VAD)
- Implementa Detección de Actividad de Voz (VAD) de ultra baja latencia.
- Permite al usuario interrumpir al asistente en cualquier momento; el sistema detiene el audio inmediatamente y vuelve al estado de escucha activa.

### 4. Control de Flujo por Voz
- Reconocimiento de intenciones para confirmación, rechazo o solicitud de explicaciones adicionales.
- **Seguridad:** Pausa automática de acciones críticas (ejecución de comandos, escritura de archivos) hasta recibir aprobación verbal del usuario.

## 🏗️ Arquitectura Técnica

El proyecto sigue una **Arquitectura Hexagonal (Puertos y Adaptadores)** para garantizar la modularidad y facilitar el intercambio de tecnologías de IA o audio.

### Componentes Core:
- **Máquina de Estados Finita (FSM):** Orquesta el ciclo de vida de la interacción (`IDLE`, `LISTENING`, `THINKING`, `SUMMARIZING`, `SPEAKING`, `WAITING_APPROVAL`).
- **Orquestador:** Maneja la lógica de negocio central y la coordinación entre adaptadores.
- **Manejo de Concurrencia:** Uso estratégico de hilos (threading) para separar la interfaz de usuario, la salida de audio interrumpible y el monitoreo constante del micrófono.

### Stack Tecnológico:
- **Lenguaje:** Python 3.10+
- **Audio I/O:** `pyaudio` / `sounddevice`
- **VAD:** `silero-vad`
- **STT/TTS:** `faster-whisper`, `piper-tts`, APIs de OpenAI y ElevenLabs.
- **LLM:** Google Generative AI (Gemini).

## 📁 Estructura del Proyecto

```text
├── core/           # Lógica principal, FSM y orquestación.
├── adapters/       # Implementaciones de STT, TTS y LLM (Patrón Strategy).
├── audio/          # Captura con VAD y reproducción interrumpible.
├── apps/           # Aplicaciones o interfaces específicas.
├── hooks/          # Hooks para integración con el sistema.
└── docs/           # Documentación detallada y registros de arquitectura.
```

## 🚀 Estado del Proyecto

El proyecto se encuentra actualmente en fase de **desarrollo (Draft/PoC)**, con una arquitectura sólida diseñada para la extensibilidad y el rendimiento en tiempo real.
