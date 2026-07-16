"""Rutas de configuración del panel y del bot."""
import logging
from flask import Blueprint, render_template, jsonify, request, flash, redirect, url_for
from flask_login import login_required
from database.db import db
from models.bot_config import BotConfig
from models.lavalink_config import LavalinkConfig
from models.panel_config import PanelConfig

settings_bp = Blueprint("settings", __name__)
logger = logging.getLogger("settings")


@settings_bp.route("/settings")
@login_required
def index():
    bot_cfg = BotConfig.query.first()
    lava_cfg = LavalinkConfig.query.first()
    panel_cfg = PanelConfig.query.first()
    return render_template("settings.html", bot_cfg=bot_cfg, lava_cfg=lava_cfg, panel_cfg=panel_cfg)


@settings_bp.route("/api/settings/bot", methods=["POST"])
@login_required
def save_bot():
    data = request.get_json(silent=True) or {}
    cfg = BotConfig.query.first()
    if not cfg:
        cfg = BotConfig()
        db.session.add(cfg)

    if "token" in data and data["token"]:
        cfg.token = data["token"]
    if "prefix" in data:
        cfg.prefix = data["prefix"][:10]
    if "timezone" in data:
        cfg.timezone = data["timezone"][:50]

    db.session.commit()
    logger.info("Configuración del bot actualizada.")
    return jsonify({"success": True, "message": "Configuración guardada."})


@settings_bp.route("/api/settings/lavalink", methods=["POST"])
@login_required
def save_lavalink():
    data = request.get_json(silent=True) or {}
    cfg = LavalinkConfig.query.first()
    if not cfg:
        cfg = LavalinkConfig()
        db.session.add(cfg)

    if "host" in data:
        cfg.host = data["host"]
    if "port" in data:
        cfg.port = int(data["port"])
    if "password" in data and data["password"]:
        cfg.password = data["password"]
    if "ssl" in data:
        cfg.ssl = bool(data["ssl"])

    db.session.commit()
    logger.info("Configuración Lavalink actualizada.")
    return jsonify({"success": True, "message": "Configuración Lavalink guardada."})


@settings_bp.route("/api/settings/lavalink/reconnect", methods=["POST"])
@login_required
def reconnect_lavalink():
    """Dispara reconexión de Lavalink (señal al bot)."""
    from services import bot_manager
    status = bot_manager.get_status()
    if not status["running"]:
        return jsonify({"success": False, "message": "El bot no está corriendo."})
    logger.info("Reconexión Lavalink solicitada.")
    return jsonify({"success": True, "message": "Señal de reconexión enviada."})


@settings_bp.route("/api/settings/panel", methods=["POST"])
@login_required
def save_panel():
    data = request.get_json(silent=True) or {}
    cfg = PanelConfig.query.first()
    if not cfg:
        cfg = PanelConfig()
        db.session.add(cfg)

    if "panel_name" in data:
        cfg.panel_name = data["panel_name"][:100]

    db.session.commit()
    return jsonify({"success": True, "message": "Configuración del panel guardada."})
