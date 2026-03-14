import subprocess
import logging
import time


class GhostTyper:
    """
    Inyecta texto y comandos de teclado apuntando directamente a la Terminal.
    Se utiliza osascript (AppleScript) para emular el tipeo.
    """

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

        # 1. Guardar el texto en el portapapeles de Mac (es mucho más confiable que simular teclas de a una)
        # Escapamos comillas simples para bash
        safe_text = text.replace("'", "'\"'\"'")
        # Nota: Usamos rstrip para asegurarnos de que no haya saltos de línea basura,
        # y usamos -n en echo para que pbcopy no agregue un newline extra.
        subprocess.run(f"echo -n '{safe_text}' | pbcopy", shell=True)

        # 2. AppleScript: Activar app -> Pegar (Cmd+V) -> Enter
        script = f'''
        tell application "{target_app}" to activate
        delay 0.2
        tell application "System Events"
            -- Simular Command + V (Pegar)
            keystroke "v" using command down
            delay 0.1
            -- Simular Enter
            key code 36
        end tell
        '''

        try:
            # Capturamos el output de error (stderr) para loggearlo bien si falla por permisos
            result = subprocess.run(
                ["osascript", "-e", script], check=True, capture_output=True, text=True
            )
            logging.info("Texto pegado y enviado con éxito.")
        except subprocess.CalledProcessError as e:
            logging.error(f"Error de Permisos en macOS inyectando texto.")
            logging.error("¡ATENCIÓN! Necesitas darle permisos a la Terminal en macOS:")
            logging.error(
                "1. Abre 'Preferencias del Sistema' -> 'Privacidad y Seguridad' -> 'Accesibilidad'"
            )
            logging.error(
                "2. Activa el interruptor para tu aplicación de Terminal (iTerm, Terminal, VSCode, Cursor, etc)."
            )
            logging.error(f"Detalle del error de AppleScript: {e.stderr.strip()}")
