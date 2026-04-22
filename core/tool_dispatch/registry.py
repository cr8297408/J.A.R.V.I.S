"""
Registry de herramientas de PC para Jarvis.

Estas son las herramientas que Gemma 4 puede invocar via function calling.
Son genéricas — funcionan con cualquier app sin adaptadores específicos.
El ScreenReaderEngine se encarga de la abstracción del SO.
"""

TOOLS: list[dict] = [
    # ── Lectura de pantalla ───────────────────────────────────────────────────
    {
        "type": "function",
        "function": {
            "name": "read_screen",
            "description": (
                "Lee en voz alta el contenido de la ventana activa o el elemento enfocado. "
                "Usar cuando el usuario pide 'leé la pantalla', 'qué hay acá', 'qué dice esto'."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "target": {
                        "type": "string",
                        "enum": ["active_window", "focused_element", "full_screen"],
                        "description": (
                            "active_window: contenido de la ventana completa. "
                            "focused_element: solo el elemento con foco. "
                            "full_screen: screenshot + descripción visual (Gemma Vision)."
                        ),
                    }
                },
                "required": ["target"],
            },
        },
    },
    # ── Navegación UI ─────────────────────────────────────────────────────────
    {
        "type": "function",
        "function": {
            "name": "navigate_ui",
            "description": (
                "Navega por la interfaz de usuario. "
                "Usar para: 'siguiente campo', 'campo anterior', 'arriba', 'abajo', 'tab'."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "direction": {
                        "type": "string",
                        "enum": ["next", "prev", "up", "down", "tab", "shift_tab"],
                    }
                },
                "required": ["direction"],
            },
        },
    },
    # ── Escritura ─────────────────────────────────────────────────────────────
    {
        "type": "function",
        "function": {
            "name": "type_text",
            "description": (
                "Escribe texto en el elemento activo (campo, celda, documento, etc.). "
                "Usar cuando el usuario quiere dictar texto o completar un campo."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "text": {"type": "string", "description": "Texto a escribir."},
                    "clear_first": {
                        "type": "boolean",
                        "description": "Si true, borra el contenido actual antes de escribir. Default: false.",
                    },
                },
                "required": ["text"],
            },
        },
    },
    # ── Apps ──────────────────────────────────────────────────────────────────
    {
        "type": "function",
        "function": {
            "name": "open_app",
            "description": "Abre una aplicación por nombre.",
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "Nombre de la aplicación. Ej: 'Excel', 'Word', 'Chrome', 'Terminal'.",
                    }
                },
                "required": ["name"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "close_app",
            "description": "Cierra la ventana activa o una aplicación por nombre.",
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "Nombre de la app. Si vacío, cierra la ventana activa.",
                    }
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "switch_window",
            "description": "Cambia el foco a otra ventana o aplicación abierta.",
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "Nombre de la app o ventana destino.",
                    }
                },
                "required": ["name"],
            },
        },
    },
    # ── Atajos de teclado ─────────────────────────────────────────────────────
    {
        "type": "function",
        "function": {
            "name": "press_shortcut",
            "description": (
                "Ejecuta un atajo de teclado. "
                "Usar para: guardar (ctrl+s), deshacer (ctrl+z), copiar (ctrl+c), etc."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "keys": {
                        "type": "string",
                        "description": "Atajo en formato 'modificador+tecla'. Ej: 'ctrl+s', 'alt+f4', 'cmd+c'.",
                    }
                },
                "required": ["keys"],
            },
        },
    },
    # ── Click en elemento ─────────────────────────────────────────────────────
    {
        "type": "function",
        "function": {
            "name": "click_element",
            "description": (
                "Hace click en un elemento descripto en lenguaje natural. "
                "Usar para: 'hacé click en Guardar', 'presioná Aceptar', 'hacé click en el menú Archivo'."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "description": {
                        "type": "string",
                        "description": "Descripción del elemento a clickear. Ej: 'botón Guardar', 'menú Archivo'.",
                    }
                },
                "required": ["description"],
            },
        },
    },
    # ── Portapapeles ──────────────────────────────────────────────────────────
    {
        "type": "function",
        "function": {
            "name": "copy_selection",
            "description": "Copia el texto seleccionado al portapapeles.",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "paste_text",
            "description": "Pega el contenido del portapapeles en el elemento activo.",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    # ── Describe pantalla ─────────────────────────────────────────────────────
    {
        "type": "function",
        "function": {
            "name": "describe_screen",
            "description": (
                "Toma un screenshot y describe visualmente lo que hay en pantalla usando Gemma Vision. "
                "Usar cuando el usuario pregunta '¿qué hay en pantalla?' o la app no tiene Accessibility API."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "focus": {
                        "type": "string",
                        "description": "Aspecto a enfatizar en la descripción. Ej: 'errores', 'botones disponibles'.",
                    }
                },
                "required": [],
            },
        },
    },
    # ── Terminal ──────────────────────────────────────────────────────────────
    {
        "type": "function",
        "function": {
            "name": "run_command",
            "description": (
                "Ejecuta un comando de terminal. REQUIERE confirmación vocal del usuario. "
                "Solo usar cuando el usuario pide explícitamente correr un comando."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "command": {
                        "type": "string",
                        "description": "Comando a ejecutar en la terminal.",
                    }
                },
                "required": ["command"],
            },
        },
    },
]

# Herramientas que requieren confirmación vocal antes de ejecutarse
REQUIRES_CONFIRMATION: frozenset[str] = frozenset({
    "run_command",
    "close_app",
})

# Atajos considerados destructivos (requieren confirmación extra)
DESTRUCTIVE_SHORTCUTS: frozenset[str] = frozenset({
    "alt+f4", "cmd+q", "ctrl+w", "ctrl+shift+w",
})
