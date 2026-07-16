"""Servicio de logging centralizado."""
import logging
from datetime import datetime, timezone
from collections import deque
from threading import Lock

# Buffer en memoria para la consola en tiempo real (máximo 500 líneas)
_log_buffer: deque[dict] = deque(maxlen=500)
_lock = Lock()


# Mensajes de werkzeug/sistema que no deben aparecer en la consola del panel
_NOISE_PATTERNS = (
    "Debugger PIN",
    "Debugger is active",
    "WARNING: This is a development server",
    "Use a production WSGI server",
    " * Running on",
    " * Restarting with",
    " * Detected change in",
)


class PanelLogHandler(logging.Handler):
    """Handler que captura logs y los almacena en buffer + BD."""

    def emit(self, record: logging.LogRecord):
        msg = record.getMessage()
        if any(pat in msg for pat in _NOISE_PATTERNS):
            return  # silenciar ruido interno de werkzeug
        entry = {
            "level": record.levelname,
            "source": record.name,
            "message": self.format(record),
            "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"),
        }
        with _lock:
            _log_buffer.append(entry)

        # Guardar en BD de forma lazy (evitar import circular)
        try:
            from database.db import db
            from models.log_entry import LogEntry
            from flask import current_app
            with current_app.app_context():
                log = LogEntry(
                    level=record.levelname,
                    source=record.name[:50],
                    message=entry["message"][:2000],
                )
                db.session.add(log)
                db.session.commit()
        except Exception:
            pass


def get_recent_logs(limit: int = 200) -> list[dict]:
    """Retorna los últimos logs del buffer en memoria."""
    with _lock:
        logs = list(_log_buffer)
    return logs[-limit:]


def setup_logging(app):
    """Configura el sistema de logging para la app Flask."""
    formatter = logging.Formatter(
        "[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    panel_handler = PanelLogHandler()
    panel_handler.setFormatter(formatter)

    # Logger raíz
    root = logging.getLogger()
    root.setLevel(logging.INFO)
    root.addHandler(panel_handler)

    # Console también
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    root.addHandler(console_handler)

    app.logger.info("Sistema de logging inicializado.")
