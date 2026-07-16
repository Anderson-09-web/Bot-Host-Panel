"""Servicio de estadísticas del sistema y del bot."""
import psutil
import time
import logging
from datetime import datetime, timezone

logger = logging.getLogger("stats")

_start_time = time.time()

# Estado compartido del bot (actualizado por bot_manager)
bot_stats: dict = {
    "running": False,
    "name": "—",
    "avatar_url": "",
    "bot_id": "—",
    "ping": 0,
    "guilds": 0,
    "users": 0,
    "uptime_seconds": 0,
    "status": "offline",   # offline | online | paused | starting
    "pid": None,
}


def get_system_stats() -> dict:
    """Retorna estadísticas de CPU, RAM y tiempo de actividad del panel."""
    cpu = psutil.cpu_percent(interval=0.1)
    mem = psutil.virtual_memory()
    uptime = int(time.time() - _start_time)

    hours, rem = divmod(uptime, 3600)
    minutes, seconds = divmod(rem, 60)

    return {
        "cpu_percent": round(cpu, 1),
        "ram_used_mb": round(mem.used / 1024 / 1024, 1),
        "ram_total_mb": round(mem.total / 1024 / 1024, 1),
        "ram_percent": round(mem.percent, 1),
        "panel_uptime": f"{hours:02d}:{minutes:02d}:{seconds:02d}",
        "panel_uptime_seconds": uptime,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


def get_full_stats() -> dict:
    """Combina estadísticas del sistema con las del bot."""
    system = get_system_stats()
    return {**system, **bot_stats}


def update_bot_stats(**kwargs):
    """Actualiza el estado global del bot."""
    global bot_stats
    bot_stats.update(kwargs)
