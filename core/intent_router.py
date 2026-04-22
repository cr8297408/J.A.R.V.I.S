"""
IntentRouter — clasifica comandos de voz en uno de los tres modos de Jarvis.

Tres modos:
    GENERAL  → conversación libre, preguntas, explicaciones (gemma4:general)
    PC       → control de cualquier app vía Accessibility API (gemma4:pc)
    CODING   → agente de programación con OpenCode + Ollama (gemma4/qwen2.5-coder)

Clasificación en cascada (sin LLM, latencia cero):
    1. Keywords de coding  → CODING
    2. Keywords de PC      → PC
    3. Fallback            → GENERAL

ModeState permite fijar el modo manualmente por voz:
    "modo código"    → todo va a CODING hasta "salir del modo"
    "modo pc"        → todo va a PC
    "modo general"   → vuelve al routing automático
"""
from __future__ import annotations

import re
import logging
from enum import Enum

logger = logging.getLogger(__name__)


class Mode(str, Enum):
    GENERAL = "general"   # Conversación libre
    PC      = "pc"        # Control de PC via Accessibility API
    CODING  = "coding"    # Agente de coding con OpenCode


# ── Keywords por modo ─────────────────────────────────────────────────────────
# El orden importa: CODING se chequea antes que PC para evitar ambigüedades
# (ej: "creá un archivo" podría matchear PC si no se chequea coding primero).

_CODING_KEYWORDS: frozenset[str] = frozenset({
    # Archivos de código
    "creá un archivo", "crear archivo", "nuevo archivo",
    "editá el archivo", "modificá el archivo", "abrí el archivo",
    "refactorizá", "refactorizar",
    # Git
    "commitear", "commit", "hacé commit", "pusheá", "push",
    "pull", "hacé pull", "branch", "nueva rama", "mergeá", "merge",
    "stash", "rebase", "cherry pick",
    # Código
    "escribí una función", "escribí una clase", "escribí un test",
    "escribí el código", "generá el código", "creá la función",
    "arreglá el bug", "fix the bug", "corregí el error",
    "agregá un método", "agregá una ruta", "agregá un endpoint",
    # Dependencias
    "instalá el paquete", "instalá la dependencia",
    "npm install", "pip install", "yarn add",
    # Tests
    "corré los tests", "ejecutá los tests", "run tests",
    "pasá los tests", "arreglá los tests",
    # Proyecto
    "modo código", "modo coding", "modo programación",
    "activá opencode", "iniciá opencode",
})

_PC_KEYWORDS: frozenset[str] = frozenset({
    # Apertura y cierre de apps
    "abrí", "abrir", "cerrá", "cerrar", "iniciá",
    "lanzá", "ejecutá la aplicación", "abrí la aplicación",
    # Lectura de pantalla
    "leé", "leer", "leeme", "leé esto", "leé la pantalla",
    "decime qué hay", "qué hay en pantalla", "describí la pantalla",
    "describí lo que hay", "describí la ventana",
    "qué dice", "qué tiene", "qué hay",
    # Navegación UI
    "pasame a", "cambiá a", "ir a", "siguiente campo",
    "campo anterior", "siguiente elemento", "elemento anterior",
    "hacé tab", "presioná tab", "scrolleá",
    "subí", "bajá", "siguiente pestaña",
    # Escritura en UI
    "escribí en el campo", "escribí en", "tipear en",
    "dictá en el campo", "completá el campo",
    # Acciones de UI
    "hacé click", "click en", "hacé doble click",
    "presioná enter", "presioná escape", "presioná el botón",
    "guardá", "guardar", "copiá", "copiar", "pegá", "pegar",
    "seleccioná todo", "seleccioná el texto",
    "borrá lo que escribí", "deshacé",
    # Ventanas
    "minimizá", "maximizá", "cerrá la ventana",
    "movete a la ventana", "cambiá de ventana",
    # Apps conocidas (sin contexto de código)
    "excel", "word", "outlook", "powerpoint",
    "explorador de archivos", "panel de control",
    "configuración del sistema",
    # Modo explícito
    "modo pc", "modo accesibilidad", "leer pantalla",
    "activá el lector de pantalla",
})

_MODE_EXIT_KEYWORDS: frozenset[str] = frozenset({
    "salir del modo", "modo general", "salí del modo",
    "modo normal", "routing automático", "desactivá el modo",
})


class ModeState:
    """
    Mantiene el modo activo de Jarvis.

    En modo ROUTING el IntentRouter clasifica cada comando.
    En cualquier otro modo, todos los comandos van al modo fijado.
    """

    def __init__(self) -> None:
        self._fixed: Mode | None = None  # None = routing automático

    @property
    def is_routing(self) -> bool:
        return self._fixed is None

    @property
    def fixed_mode(self) -> Mode | None:
        return self._fixed

    def fix(self, mode: Mode) -> None:
        self._fixed = mode
        logger.info(f"Modo fijado: {mode.value}")

    def release(self) -> None:
        self._fixed = None
        logger.info("Routing automático activado.")


class IntentRouter:
    """
    Clasifica un texto de voz en Mode.GENERAL, Mode.PC o Mode.CODING.

    Uso:
        router = IntentRouter()
        mode = router.route("creá un archivo utils.py")  # → Mode.CODING
        mode = router.route("abrí Excel")                # → Mode.PC
        mode = router.route("qué es una promesa en JS")  # → Mode.GENERAL
    """

    def __init__(self, state: ModeState | None = None) -> None:
        self.state = state or ModeState()

    def route(self, text: str) -> Mode:
        """
        Clasifica el texto y devuelve el modo correspondiente.
        Respeta el ModeState si hay un modo fijado.
        """
        normalized = self._normalize(text)

        # 1. Chequear si el usuario quiere salir del modo fijado
        if self._matches(normalized, _MODE_EXIT_KEYWORDS):
            self.state.release()
            logger.debug(f"route: salida de modo → GENERAL")
            return Mode.GENERAL

        # 2. Si hay modo fijado, usarlo directamente
        if not self.state.is_routing:
            logger.debug(f"route: modo fijado → {self.state.fixed_mode.value}")
            return self.state.fixed_mode  # type: ignore[return-value]

        # 3. Routing automático por keywords
        mode = self._classify(normalized, text)

        # 4. Fijar modo si el usuario lo pidió explícitamente
        if "modo código" in normalized or "modo coding" in normalized or "modo programación" in normalized:
            self.state.fix(Mode.CODING)
        elif "modo pc" in normalized or "modo accesibilidad" in normalized:
            self.state.fix(Mode.PC)

        logger.debug(f"route: '{text[:50]}' → {mode.value}")
        return mode

    def _classify(self, normalized: str, original: str) -> Mode:
        # Coding primero — tiene keywords más específicos
        if self._matches(normalized, _CODING_KEYWORDS):
            return Mode.CODING

        # PC control — keywords de interacción con UI
        if self._matches(normalized, _PC_KEYWORDS):
            return Mode.PC

        # Heurística adicional: extensiones de archivo típicas de código
        if re.search(r"\.(py|js|ts|go|rs|java|cpp|c|rb|php|swift|kt)\b", original):
            return Mode.CODING

        return Mode.GENERAL

    @staticmethod
    def _normalize(text: str) -> str:
        """Normaliza texto para comparación: minúsculas, sin puntuación extra."""
        return text.lower().strip()

    @staticmethod
    def _matches(normalized: str, keywords: frozenset[str]) -> bool:
        return any(kw in normalized for kw in keywords)
