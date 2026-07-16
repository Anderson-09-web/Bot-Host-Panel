"""Rutas del dashboard principal."""
import logging
from flask import Blueprint, render_template, jsonify
from flask_login import login_required
from services.stats_service import get_full_stats
from services import bot_manager

dashboard_bp = Blueprint("dashboard", __name__)
logger = logging.getLogger("dashboard")


@dashboard_bp.route("/")
@login_required
def index():
    stats = get_full_stats()
    bot_status = bot_manager.get_status()
    return render_template("dashboard.html", stats=stats, bot_status=bot_status)


@dashboard_bp.route("/api/stats")
@login_required
def api_stats():
    """Endpoint JSON para actualización en tiempo real."""
    return jsonify(get_full_stats())


@dashboard_bp.route("/api/bot/start", methods=["POST"])
@login_required
def bot_start():
    result = bot_manager.start_bot()
    return jsonify(result)


@dashboard_bp.route("/api/bot/pause", methods=["POST"])
@login_required
def bot_pause():
    status = bot_manager.get_status()
    if status["paused"]:
        result = bot_manager.resume_bot()
    else:
        result = bot_manager.pause_bot()
    return jsonify(result)


@dashboard_bp.route("/api/bot/restart", methods=["POST"])
@login_required
def bot_restart():
    result = bot_manager.restart_bot()
    return jsonify(result)


@dashboard_bp.route("/api/bot/stop", methods=["POST"])
@login_required
def bot_stop():
    result = bot_manager.stop_bot()
    return jsonify(result)


@dashboard_bp.route("/api/bot/status")
@login_required
def bot_status():
    return jsonify(bot_manager.get_status())
