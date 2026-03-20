# 🎙️ J.A.R.V.I.S. (Gemini Speech Extension) Installation Guide

Esta guía explica cómo instalar y ejecutar la extensión de voz J.A.R.V.I.S. para el `gemini-cli` en macOS y Linux.

## ⚡ Instalación Automática (Recomendada)

Hemos incluido un script de instalación que detecta automáticamente tu sistema operativo (macOS o Linux), instala las dependencias del sistema necesarias, configura el entorno virtual de Python e instala la CLI de Gemini.

### 1. Ejecutar el Instalador
Abre tu terminal en la raíz del proyecto y ejecuta:

```bash
./install.sh
```

**¿Qué hace este script?**
1. Instala `portaudio` (requerido para capturar audio del micrófono). En Mac usa Homebrew, en Linux usa `apt`, `pacman` o `dnf`.
2. Verifica que `Node.js` esté instalado (necesario para la CLI).
3. Instala `@google/generative-ai-cli` globalmente usando `npm`.
4. Crea un entorno virtual de Python 3 (`.venv`).
5. Instala las dependencias necesarias dentro del entorno virtual (`requirements.txt`).
6. Copia el archivo de configuración `.env.example` a `.env`.
7. **Crea el comando global `jarvis`** en tu sistema (`/usr/local/bin/jarvis`) para que puedas iniciarlo desde cualquier lugar.

---

## ⚙️ Configuración (Post-Instalación)

### 1. Configurar las API Keys
Abre el archivo `.env` en la raíz del proyecto y añade tus claves de API. J.A.R.V.I.S. utiliza modelos LLM rápidos (como Groq) para procesar y filtrar las respuestas antes de hablar.

```env
# Ejemplo de .env
ACTIVE_BRAIN_ENGINE=groq
GROQ_API_KEY=tu_clave_de_groq_aqui
```

### 2. Configurar los Hooks de Gemini CLI
Para que J.A.R.V.I.S. pueda interceptar los eventos de la terminal de Gemini (como peticiones de permisos de herramientas), necesitas indicarle a la CLI dónde está el hook de notificaciones.

Edita tu archivo de configuración de Gemini CLI (usualmente en `~/.gemini/settings.json`) y asegúrate de que los hooks apunten al script de este proyecto:

```json
{
  "hooks": {
    "notification": "/Ruta/Absoluta/A/gemini-extension-spech/hooks/notification.py"
  }
}
```
*(Asegúrate de cambiar `/Ruta/Absoluta/A/...` por la ruta real donde clonaste este repositorio).*

---

## 🚀 Cómo Usar J.A.R.V.I.S.

Una vez instalado, el script te habrá creado un comando global. Así que puedes ir a cualquier proyecto, carpeta o repositorio de tu computadora, abrir una terminal y simplemente escribir:

```bash
jarvis
```

Esto hará lo siguiente de forma automática:
1. Navegará internamente a su propia carpeta de instalación y activará el entorno `.venv`.
2. Arrancará el motor de detección de voz (VAD) esperando la palabra clave *"Hey Jarvis"*.
3. Abrirá **automáticamente una nueva ventana de terminal** limpia, en la misma carpeta desde donde invocaste el comando, con `gemini` corriendo y listo para recibir tus instrucciones por voz.

### Comandos de Voz:
- **"Hey Jarvis"**: Activa el micrófono para escuchar tu petición.
- **[Aprobación de Herramientas]**: Cuando Jarvis te pida autorización para ejecutar un comando (Barge-in soportado), simplemente di en voz alta *"Uno"* (Permitir una vez), *"Dos"* (Permitir sesión) o *"Tres"* (Denegar). No necesitas decir "Hey Jarvis" para estas aprobaciones, él ya estará escuchando.
- **Interrupciones (Barge-in)**: Si Jarvis está hablando y quieres interrumpirlo, simplemente habla (por ejemplo, dando una aprobación) y él se silenciará automáticamente.

---

## 🛠️ Solución de Problemas Frecuentes

- **Error `No module named edge_tts`**: Asegúrate de haber ejecutado `./install.sh` sin errores para que el `.venv` se haya creado correctamente.
- **Error de permisos en macOS (AppleScript 1002)**: Si Jarvis no puede inyectar texto en la terminal, ve a *Preferencias del Sistema -> Privacidad y Seguridad -> Accesibilidad* y otorga permisos a tu aplicación de Terminal (iTerm, Terminal, etc.). Jarvis te avisará en voz alta si esto ocurre.
- **Dependencias de STT en Linux**: Actualmente, el proyecto usa `mlx-whisper` para transcripción local rápida, el cual está optimizado para Apple Silicon (Mac). Si estás en Linux, el STT puede requerir adaptaciones a OpenAI Whisper estándar.