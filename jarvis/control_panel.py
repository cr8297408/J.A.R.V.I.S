"""
J.A.R.V.I.S. Control Panel — ventana flotante con logs en tiempo real y push-to-talk.

Diseño:
  - Fondo oscuro estilo JARVIS
  - Área de logs con colores por nivel (INFO/WARNING/ERROR)
  - Botón grande "Hablar" que dispara grabación sin necesitar wake word
  - Indicador de estado animado (Standby / Escuchando / Pensando / Hablando)

Thread safety:
  - LogQueueHandler pone registros en una Queue
  - root.after(100, _poll) los lee y actualiza el Text widget en el hilo de tkinter
  - El botón "Hablar" setea active_listening_requested desde cualquier hilo
"""
from __future__ import annotations

import logging
import queue
import threading
import tkinter as tk
from tkinter import font as tkfont
from typing import Callable

logger = logging.getLogger(__name__)

# ── Paleta de colores ──────────────────────────────────────────────────────────
_BG         = "#0d1117"   # fondo principal
_BG2        = "#161b22"   # fondo secundario (área de logs)
_ACCENT     = "#1f6feb"   # azul JARVIS
_GREEN      = "#3fb950"   # verde OK / hablando
_YELLOW     = "#d29922"   # amarillo warning / pensando
_RED        = "#f85149"   # rojo error / escuchando
_FG         = "#c9d1d9"   # texto principal
_FG_DIM     = "#8b949e"   # texto secundario
_BTN_ACTIVE = "#238636"   # verde botón activo
_BTN_IDLE   = "#1f6feb"   # azul botón idle
_BTN_REC    = "#da3633"   # rojo mientras graba

# Colores por nivel de log
_LEVEL_COLORS = {
    "DEBUG":    _FG_DIM,
    "INFO":     _FG,
    "WARNING":  _YELLOW,
    "ERROR":    _RED,
    "CRITICAL": _RED,
}


# ── Handler de logging que alimenta la Queue ───────────────────────────────────

class LogQueueHandler(logging.Handler):
    """Logging handler que manda registros a una Queue para consumo en tkinter."""

    def __init__(self, log_queue: queue.Queue) -> None:
        super().__init__()
        self._queue = log_queue

    def emit(self, record: logging.LogRecord) -> None:
        try:
            self._queue.put_nowait(record)
        except queue.Full:
            pass


# ── Estado del daemon (leído por el panel) ────────────────────────────────────

class DaemonState:
    """Puente de estado entre el daemon y el panel. Thread-safe."""

    STANDBY    = "standby"
    LISTENING  = "listening"
    THINKING   = "thinking"
    SPEAKING   = "speaking"

    def __init__(self) -> None:
        self._state = self.STANDBY
        self._lock  = threading.Lock()

    @property
    def value(self) -> str:
        with self._lock:
            return self._state

    @value.setter
    def value(self, s: str) -> None:
        with self._lock:
            self._state = s


# Singleton compartido — importable desde el daemon y el panel
daemon_state = DaemonState()


# ── Panel de control ───────────────────────────────────────────────────────────

class ControlPanel:
    """
    Ventana tkinter flotante con logs y push-to-talk.

    Uso:
        panel = ControlPanel()
        panel.show()        # Mostrar / traer al frente
        panel.mainloop()    # Iniciar event loop (llamar desde el hilo principal)
    """

    def __init__(
        self,
        trigger_recording: Callable[[], None] | None = None,
        max_log_lines: int = 500,
    ) -> None:
        """
        Args:
            trigger_recording: callback que se llama al presionar "Hablar".
                               Debe ser thread-safe (se llama desde el hilo tkinter).
            max_log_lines: cuántas líneas mantener antes de hacer trim.
        """
        self._trigger   = trigger_recording
        self._max_lines = max_log_lines
        self._log_queue: queue.Queue = queue.Queue(maxsize=1000)
        self._recording = False

        self._build_ui()
        self._install_log_handler()
        self._schedule_poll()

    # ── Construcción UI ───────────────────────────────────────────────────────

    def _build_ui(self) -> None:
        self.root = tk.Tk()
        self.root.title("J.A.R.V.I.S — Panel de Control")
        self.root.configure(bg=_BG)
        self.root.geometry("700x520")
        self.root.minsize(500, 380)
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

        # Centrar en pantalla
        self.root.update_idletasks()
        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()
        w, h = 700, 520
        self.root.geometry(f"{w}x{h}+{(sw-w)//2}+{(sh-h)//2}")

        mono = tkfont.Font(family="Menlo", size=11)

        # ── Header ────────────────────────────────────────────────────────────
        hdr = tk.Frame(self.root, bg=_BG, pady=8)
        hdr.pack(fill="x", padx=16)

        tk.Label(
            hdr, text="J.A.R.V.I.S", bg=_BG, fg=_ACCENT,
            font=("Helvetica Neue", 18, "bold"),
        ).pack(side="left")

        # Estado: punto + texto
        self._state_dot  = tk.Label(hdr, text="●", bg=_BG, fg=_FG_DIM, font=("Helvetica Neue", 16))
        self._state_dot.pack(side="right", padx=(0, 4))
        self._state_label = tk.Label(hdr, text="Standby", bg=_BG, fg=_FG_DIM, font=("Helvetica Neue", 13))
        self._state_label.pack(side="right", padx=(0, 8))

        tk.Frame(self.root, bg=_ACCENT, height=1).pack(fill="x", padx=16)

        # ── Área de logs ──────────────────────────────────────────────────────
        log_frame = tk.Frame(self.root, bg=_BG2, padx=2, pady=2)
        log_frame.pack(fill="both", expand=True, padx=16, pady=(10, 6))

        self._log_text = tk.Text(
            log_frame,
            bg=_BG2, fg=_FG,
            font=mono,
            state="disabled",
            wrap="word",
            relief="flat",
            selectbackground=_ACCENT,
            insertbackground=_FG,
            pady=4, padx=6,
        )

        scrollbar = tk.Scrollbar(log_frame, command=self._log_text.yview, bg=_BG2)
        self._log_text.configure(yscrollcommand=scrollbar.set)

        scrollbar.pack(side="right", fill="y")
        self._log_text.pack(side="left", fill="both", expand=True)

        # Configurar tags de colores por nivel
        for level, color in _LEVEL_COLORS.items():
            self._log_text.tag_configure(level, foreground=color)
        self._log_text.tag_configure("TIMESTAMP", foreground=_FG_DIM)

        # ── Footer: auto-scroll + botón hablar ────────────────────────────────
        footer = tk.Frame(self.root, bg=_BG, pady=8)
        footer.pack(fill="x", padx=16)

        self._autoscroll_var = tk.BooleanVar(value=True)
        tk.Checkbutton(
            footer, text="Auto-scroll", variable=self._autoscroll_var,
            bg=_BG, fg=_FG_DIM, activebackground=_BG, activeforeground=_FG,
            selectcolor=_BG2, relief="flat",
        ).pack(side="left")

        tk.Button(
            footer, text="🗑  Limpiar", command=self._clear_logs,
            bg=_BG2, fg=_FG_DIM, activebackground=_BG, activeforeground=_FG,
            relief="flat", padx=8, pady=4, cursor="hand2",
        ).pack(side="left", padx=(8, 0))

        # Botón hablar — grande y prominente
        self._btn = tk.Button(
            footer,
            text="🎙  HABLAR",
            command=self._on_talk_pressed,
            bg=_BTN_IDLE, fg="white",
            activebackground=_BTN_ACTIVE, activeforeground="white",
            relief="flat", padx=20, pady=8,
            font=("Helvetica Neue", 13, "bold"),
            cursor="hand2",
        )
        self._btn.pack(side="right")

    # ── Logging ───────────────────────────────────────────────────────────────

    def _install_log_handler(self) -> None:
        handler = LogQueueHandler(self._log_queue)
        handler.setLevel(logging.DEBUG)
        handler.setFormatter(logging.Formatter("%(asctime)s  %(levelname)-8s  %(message)s", "%H:%M:%S"))
        logging.getLogger().addHandler(handler)

    def _schedule_poll(self) -> None:
        self.root.after(100, self._poll_logs)

    def _poll_logs(self) -> None:
        """Consume la queue y actualiza el Text widget. Se llama cada 100ms."""
        try:
            while True:
                record = self._log_queue.get_nowait()
                self._append_log(record)
        except queue.Empty:
            pass

        self._update_state_indicator()
        self.root.after(100, self._poll_logs)

    def _append_log(self, record: logging.LogRecord) -> None:
        self._log_text.configure(state="normal")

        ts    = f"{record.asctime if hasattr(record, 'asctime') else '??:??:??'}"
        level = record.levelname
        msg   = record.getMessage()

        # Formatear timestamp
        # record.asctime puede no estar si el formatter no lo generó — forzamos
        import time
        ts = time.strftime("%H:%M:%S", time.localtime(record.created))

        self._log_text.insert("end", f"{ts}  ", "TIMESTAMP")
        self._log_text.insert("end", f"{level:<8}  ", level)
        self._log_text.insert("end", f"{msg}\n", level)

        # Trim si hay demasiadas líneas
        lines = int(self._log_text.index("end-1c").split(".")[0])
        if lines > self._max_lines:
            self._log_text.delete("1.0", f"{lines - self._max_lines}.0")

        self._log_text.configure(state="disabled")

        if self._autoscroll_var.get():
            self._log_text.see("end")

    def _clear_logs(self) -> None:
        self._log_text.configure(state="normal")
        self._log_text.delete("1.0", "end")
        self._log_text.configure(state="disabled")

    # ── Estado ────────────────────────────────────────────────────────────────

    def _update_state_indicator(self) -> None:
        state = daemon_state.value
        cfg = {
            DaemonState.STANDBY:   ("Standby",    _FG_DIM),
            DaemonState.LISTENING: ("Escuchando", _RED),
            DaemonState.THINKING:  ("Pensando",   _YELLOW),
            DaemonState.SPEAKING:  ("Hablando",   _GREEN),
        }
        label, color = cfg.get(state, ("Standby", _FG_DIM))
        self._state_label.configure(text=label, fg=color)
        self._state_dot.configure(fg=color)

        # Actualizar botón si está grabando
        if self._recording:
            self._btn.configure(bg=_BTN_REC, text="⏹  GRABANDO...")
        else:
            self._btn.configure(bg=_BTN_IDLE, text="🎙  HABLAR")

    # ── Push-to-talk ──────────────────────────────────────────────────────────

    def _on_talk_pressed(self) -> None:
        if self._recording:
            return  # Doble click — ignorar

        self._recording = True
        daemon_state.value = DaemonState.LISTENING
        self._btn.configure(bg=_BTN_REC, text="⏹  GRABANDO...", state="disabled")
        logger.info("[Panel] Push-to-talk activado")

        if self._trigger:
            # Llamar en hilo separado para no bloquear la UI
            threading.Thread(target=self._trigger, daemon=True).start()

        # Resetear botón después de 4s (el VAD detecta silencio solo)
        self.root.after(4000, self._reset_btn)

    def _reset_btn(self) -> None:
        self._recording = False
        self._btn.configure(state="normal")

    # ── Ventana ───────────────────────────────────────────────────────────────

    def _on_close(self) -> None:
        """Ocultar en lugar de destruir — el panel sigue vivo para reabrirse."""
        self.root.withdraw()

    def show(self) -> None:
        """Mostrar o traer al frente."""
        self.root.deiconify()
        self.root.lift()
        self.root.focus_force()

    def mainloop(self) -> None:
        """Iniciar el event loop de tkinter. Llamar desde el hilo principal."""
        self.root.mainloop()
