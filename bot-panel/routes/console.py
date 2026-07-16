"""Rutas de consola en tiempo real."""
import logging
from flask import Blueprint, render_template, jsonify, Response
from flask_login import login_required
from services.log_service import get_recent_logs
import time
import json

console_bp = Blueprint("console", __name__)
logger = logging.getLogger("console")


@console_bp.route("/console")
@login_required
def index():
    return render_template("console.html")


@console_bp.route("/api/console/logs")
@login_required
def api_logs():
    """Retorna los logs recientes en JSON."""
    logs = get_recent_logs(200)
    return jsonify({"logs": logs})


@console_bp.route("/api/console/stream")
@login_required
def stream():
    """Server-Sent Events para consola en tiempo real."""
    def generate():
        last_count = 0
        while True:
            logs = get_recent_logs(200)
            if len(logs) > last_count:
                new_logs = logs[last_count:]
                last_count = len(logs)
                for entry in new_logs:
                    yield f"data: {json.dumps(entry)}\n\n"
            time.sleep(0.5)

    return Response(generate(), mimetype="text/event-stream",
                    headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})
