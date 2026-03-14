# Jarvis Voice Approvals

## Visión General
Jarvis permite gestionar de forma interactiva y mediante voz los permisos de ejecución de herramientas que requiere el CLI de Gemini (los prompts de "Action Required").

Cuando el CLI de Gemini intenta ejecutar un comando sensible en la terminal, pausa la ejecución y solicita confirmación del usuario:
1. Allow once (Permitir una vez)
2. Allow for this session (Permitir para esta sesión)
3. Deny (Denegar)

Jarvis intercepta esta solicitud, la lee en voz alta mediante TTS y permite responder de forma natural usando la voz.

## Arquitectura

La implementación consta de los siguientes componentes:

1. **`hooks/notification.py`**: 
   - Un script registrado en `.gemini/settings.json` bajo el evento `Notification`.
   - Su función es escuchar notificaciones internas del CLI de Gemini.
   - Cuando detecta un payload del tipo `{"notification_type": "ToolPermission"}`, envía una alerta por TCP al Daemon de Jarvis con el prefijo `__NOTIFICATION__`.

2. **`core/server/jarvis_daemon.py`**:
   - Intercepta los mensajes con prefijo `__NOTIFICATION__`.
   - Reproduce un aviso por voz (TTS): *"Tool permission required. Say 1 to allow once, 2 to allow for this session, or 3 to deny."*
   - Activa una bandera interna (`awaiting_tool_permission.set()`) para avisarle al motor de voz que el sistema está esperando una respuesta numérica.

3. **`core/audio/vad_listener.py` & `GhostTyper`**:
   - Cuando el usuario habla, el STT transcribe el audio.
   - Si la bandera `awaiting_tool_permission` está activa, el listener analiza el texto en busca de palabras clave de aprobación/denegación.
   - Traduce comandos naturales a opciones numéricas:
     - **Opción 1:** "uno", "one", "una vez", "once", "sí", "si", "yes" -> `1`
     - **Opción 2:** "dos", "two", "sesión", "session", "siempre", "always" -> `2`
     - **Opción 3:** "tres", "three", "no", "denegar", "deny" -> `3`
   - Envía el número correspondiente a la terminal dedicada usando `GhostTyper` (presionando `Enter` automáticamente) y reinicia la bandera.

## Uso

1. Pídele a Gemini que ejecute un comando (ej. "Lista los archivos del directorio").
2. Gemini preparará el comando y se pausará, mostrando las opciones en la terminal.
3. Escucharás a Jarvis avisarte que se requiere un permiso.
4. Responde de forma natural ("Sí", "Permitir siempre", "No", etc.).
5. Jarvis insertará el número correcto y continuará la ejecución.