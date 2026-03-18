import subprocess
import logging
import time
import os


class GhostTyper:
    """
    Inyecta texto y comandos de teclado apuntando directamente a la Terminal.
    Se utiliza osascript (AppleScript) para emular el tipeo.
    """

    @staticmethod
    def launch_gemini_terminal(target_app: str = "Terminal"):
        """
        Abre una nueva ventana de la Terminal ejecutando el comando gemini.
        Se asegura de abrir en la misma ruta donde se inició el Daemon.
        """
        logging.info(f"Abriendo una nueva ventana de {target_app} con gemini cli...")

        # Obtener la ruta actual donde se está ejecutando el daemon
        cwd = os.getcwd()

        # Usar AppleScript para abrir una sola ventana en la ruta correcta.
        # Agregamos "exit" al final para que la ventana pueda cerrarse si el proceso muere.
        script = f'''
        tell application "{target_app}"
            if not (exists window 1) then reopen
            activate
            delay 0.5
            
            -- Si la ventana activa está libre (ej. recién iniciada la app), la usamos.
            -- Si está ocupada (ej. corriendo el daemon o cualquier otra cosa), abrimos otra.
            if not busy of window 1 then
                do script "cd '{cwd}' && clear && gemini; exit" in window 1
            else
                do script "cd '{cwd}' && clear && gemini; exit"
            end if
        end tell
        '''
        try:
            subprocess.run(
                ["osascript", "-e", script], check=True, capture_output=True, text=True
            )
            logging.info("Terminal con Gemini abierta en el directorio correcto.")
            # Esperamos un momento a que inicialice Gemini antes de que el usuario hable
            time.sleep(2)
        except subprocess.CalledProcessError as e:
            logging.error(
                f"Error abriendo la Terminal con AppleScript: {e.stderr.strip()}"
            )

    @staticmethod
    def type_string(text: str, target_app: str = "Terminal"):
        """
        Trae la aplicación objetivo al frente, pega el string y aprieta Enter.
        Usamos el portapapeles (clipboard) temporalmente en lugar de 'keystroke'
        caracter por caracter para evitar que macOS se coma los espacios si la CPU está ocupada.
        """
        if not text:
            return

        logging.info(f"GhostTyper inyectando en {target_app}: '{text}'")

        # Enviar comando para abrir gemini si se nos pide
        # O detectar si queremos abrir una ventana dedicada, pero por ahora abrimos la terminal
        # y si no hay ventana, el script de arriba crea una.

        # 1. Guardar el texto en el portapapeles de Mac (es mucho más confiable que simular teclas de a una)
        # Escapamos comillas simples para bash
        safe_text = text.replace("'", "'\"'\"'")
        # Nota: quitamos el \n del final en el portapapeles para evitar que herramientas como prompt-toolkit
        # abran un bloque multilínea que ignora el Enter normal.
        subprocess.run(f"echo -n '{safe_text}' | pbcopy", shell=True)

        # 2. AppleScript: Activar app -> Pegar (Cmd+V) -> Enter
        script = f'''
        tell application "{target_app}"
            if not (exists window 1) then
                reopen
            end if
            activate
            delay 0.3
        end tell
        
        tell application "System Events"
            -- Simular Command + V (Pegar)
            keystroke "v" using command down
            -- Darle tiempo a la terminal para procesar el texto (evita que el enter llegue antes que la UI actualice)
            delay 0.5
            -- Usar explícitamente "keystroke return" en lugar de "key code 36" para mayor compatibilidad
            keystroke return
            -- En caso de bracketed paste mode, un segundo return puede ser necesario
            delay 0.5
            keystroke return
        end tell
        '''

        try:
            # Capturamos el output de error (stderr) para loggearlo bien si falla por permisos
            result = subprocess.run(
                ["osascript", "-e", script], check=True, capture_output=True, text=True
            )
            logging.info("Texto pegado y enviado con éxito.")
        except subprocess.CalledProcessError as e:
            error_msg = e.stderr.strip()
            logging.error(f"Error de Permisos en macOS inyectando texto.")
            logging.error("¡ATENCIÓN! Necesitas darle permisos a la Terminal en macOS:")
            logging.error(
                "1. Abre 'Preferencias del Sistema' -> 'Privacidad y Seguridad' -> 'Accesibilidad'"
            )
            logging.error(
                "2. Activa el interruptor para tu aplicación de Terminal (iTerm, Terminal, VSCode, Cursor, etc)."
            )
            logging.error(f"Detalle del error de AppleScript: {error_msg}")

            if (
                "1002" in error_msg
                or "no tiene permitido" in error_msg
                or "not allowed" in error_msg
            ):
                try:
                    from adapters.tts.mac_say_tts import MacSayTTS
                    import threading

                    logging.info(
                        "Avisando al usuario por voz sobre el problema de permisos..."
                    )
                    tts = MacSayTTS()
                    dummy_event = threading.Event()
                    tts.speak(
                        "Señor, mis protocolos de escritura están bloqueados. Necesito permisos de accesibilidad en las preferencias del sistema para poder escribir por usted.",
                        dummy_event,
                    )
                except Exception as ex:
                    logging.error(f"Error reproduciendo aviso de TTS: {ex}")
