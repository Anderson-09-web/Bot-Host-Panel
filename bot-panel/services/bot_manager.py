"""
Gestor del proceso del bot de Discord.
Controla inicio, pausa, reinicio y detención usando subprocess.
"""
import subprocess
import signal
import os
import sys
import time
import logging
import threading
from services.stats_service import update_bot_stats

logger = logging.getLogger("bot_manager")

_process: subprocess.Popen | None = None
_log_thread: threading.Thread | None = None
_paused = False
_lock = threading.Lock()


def _stream_logs(proc: subprocess.Popen):
    """Lee stdout/stderr del proceso bot y los envía al logger."""
    try:
        for line in iter(proc.stdout.readline, b""):
            decoded = line.decode("utf-8", errors="replace").rstrip()
            if decoded:
                logger.info(f"[BOT] {decoded}")
    except Exception as e:
        logger.warning(f"[BOT] Error leyendo stdout: {e}")


def get_status() -> dict:
    """Retorna el estado actual del proceso."""
    global _process, _paused
    with _lock:
        running = _process is not None and _process.poll() is None
        return {
            "running": running,
            "paused": _paused if running else False,
            "pid": _process.pid if running else None,
            "status": (
                "paused" if (_paused and running)
                else "online" if running
                else "offline"
            ),
        }


def start_bot(bot_script: str = "bot.py") -> dict:
    """Inicia el proceso del bot."""
    global _process, _log_thread, _paused

    with _lock:
        if _process and _process.poll() is None:
            return {"success": False, "message": "El bot ya está corriendo."}

        bot_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), bot_script)
        if not os.path.exists(bot_path):
            return {"success": False, "message": f"No se encontró {bot_script}"}

        try:
            _process = subprocess.Popen(
                [sys.executable, bot_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                cwd=os.path.dirname(bot_path),
                env=os.environ.copy(),
            )
            _paused = False
            _log_thread = threading.Thread(target=_stream_logs, args=(_process,), daemon=True)
            _log_thread.start()

            update_bot_stats(running=True, status="online", pid=_process.pid)
            logger.info(f"Bot iniciado con PID {_process.pid}")
            return {"success": True, "message": f"Bot iniciado (PID {_process.pid})"}
        except Exception as e:
            logger.error(f"Error al iniciar el bot: {e}")
            return {"success": False, "message": str(e)}


def pause_bot() -> dict:
    """Envía SIGSTOP al proceso para pausarlo."""
    global _paused
    with _lock:
        if not _process or _process.poll() is not None:
            return {"success": False, "message": "El bot no está corriendo."}
        try:
            os.kill(_process.pid, signal.SIGSTOP)
            _paused = True
            update_bot_stats(status="paused")
            logger.info("Bot pausado.")
            return {"success": True, "message": "Bot pausado."}
        except Exception as e:
            return {"success": False, "message": str(e)}


def resume_bot() -> dict:
    """Reanuda el proceso pausado con SIGCONT."""
    global _paused
    with _lock:
        if not _process or _process.poll() is not None:
            return {"success": False, "message": "El bot no está corriendo."}
        try:
            os.kill(_process.pid, signal.SIGCONT)
            _paused = False
            update_bot_stats(status="online")
            logger.info("Bot reanudado.")
            return {"success": True, "message": "Bot reanudado."}
        except Exception as e:
            return {"success": False, "message": str(e)}


def restart_bot(bot_script: str = "bot.py") -> dict:
    """Detiene y reinicia el bot."""
    stop_result = stop_bot()
    time.sleep(1.5)
    return start_bot(bot_script)


def stop_bot() -> dict:
    """Detiene el proceso del bot."""
    global _process, _paused
    with _lock:
        if not _process or _process.poll() is not None:
            _process = None
            update_bot_stats(running=False, status="offline", pid=None)
            return {"success": False, "message": "El bot no está corriendo."}
        try:
            _process.terminate()
            try:
                _process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                _process.kill()
            _process = None
            _paused = False
            update_bot_stats(running=False, status="offline", pid=None)
            logger.info("Bot detenido.")
            return {"success": True, "message": "Bot detenido."}
        except Exception as e:
            logger.error(f"Error al detener el bot: {e}")
            return {"success": False, "message": str(e)}
