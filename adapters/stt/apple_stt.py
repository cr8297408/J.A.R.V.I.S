"""
AppleSpeechSTT — STT nativo de macOS usando SFSpeechRecognizer.

Misma tecnología que Siri. Corre en el Neural Engine de Apple Silicon,
cero descarga, latencia < 1s, soporte nativo para español argentino.

Requiere:
  pip install pyobjc-framework-Speech
  Permiso de "Reconocimiento de voz" en Preferencias > Privacidad.
"""
from __future__ import annotations

import logging
import threading

logger = logging.getLogger(__name__)


class AppleSpeechSTT:
    """STT usando SFSpeechRecognizer de macOS. Sin modelo que descargar."""

    def __init__(self, locale: str = "es-AR") -> None:
        import Foundation
        import Speech

        ns_locale = Foundation.NSLocale.localeWithLocaleIdentifier_(locale)
        self._recognizer = Speech.SFSpeechRecognizer.alloc().initWithLocale_(ns_locale)

        if not self._recognizer:
            raise RuntimeError(
                f"SFSpeechRecognizer no disponible para locale '{locale}'. "
                "Verificá que el idioma esté instalado en el sistema."
            )

        if not self._recognizer.isAvailable():
            raise RuntimeError(
                "SFSpeechRecognizer no disponible. "
                "Revisá Preferencias > Privacidad > Reconocimiento de voz."
            )

        logger.info("[AppleSpeechSTT] Listo — locale: %s", locale)

    @staticmethod
    def request_authorization() -> bool:
        """Solicita permiso al usuario para reconocimiento de voz. Bloqueante."""
        import Speech

        authorized = []
        done = threading.Event()

        def callback(status):
            # SFSpeechRecognizerAuthorizationStatusAuthorized == 3
            authorized.append(status == 3)
            done.set()

        Speech.SFSpeechRecognizer.requestAuthorization_(callback)
        done.wait(timeout=15.0)
        return authorized[0] if authorized else False

    @staticmethod
    def is_available() -> bool:
        """True si pyobjc-framework-Speech está instalado y el sistema lo soporta."""
        try:
            import Speech  # noqa: F401
            import Foundation  # noqa: F401
            return True
        except ImportError:
            return False

    def transcribe(self, audio_file_path: str) -> str:
        """Toma un .wav y devuelve la transcripción. Bloqueante hasta obtener resultado final."""
        import Foundation
        import Speech

        url = Foundation.NSURL.fileURLWithPath_(audio_file_path)
        request = Speech.SFSpeechURLRecognitionRequest.alloc().initWithURL_(url)
        request.setShouldReportPartialResults_(False)

        result_text: list[str] = []
        done = threading.Event()

        def handler(result, error):
            if error:
                logger.warning("[AppleSpeechSTT] Error de reconocimiento: %s", error)
            elif result is not None and result.isFinal():
                text = result.bestTranscription().formattedString()
                if text:
                    result_text.append(text)
            done.set()

        self._recognizer.recognitionTaskWithRequest_resultHandler_(request, handler)

        # SFSpeechRecognizer entrega callbacks via NSRunLoop.
        # En un hilo background sin event loop de Cocoa, el callback nunca llega
        # si usamos threading.Event.wait() puro. Hay que spinear el run loop.
        import time
        deadline = time.monotonic() + 10.0
        run_loop = Foundation.NSRunLoop.currentRunLoop()
        while not done.is_set() and time.monotonic() < deadline:
            run_loop.runUntilDate_(Foundation.NSDate.dateWithTimeIntervalSinceNow_(0.05))

        return result_text[0].strip() if result_text else ""
