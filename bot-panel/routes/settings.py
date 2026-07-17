"""Rutas de configuración del panel y del bot."""
import os
import logging
from flask import Blueprint, render_template, jsonify, request, flash, redirect, url_for
from flask_login import login_required
from database.db import db
from models.bot_config import BotConfig
from models.lavalink_config import LavalinkConfig
from models.panel_config import PanelConfig
from models.env_variable import EnvVariable

settings_bp = Blueprint("settings", __name__)
logger = logging.getLogger("settings")


@settings_bp.route("/settings")
@login_required
def index():
    bot_cfg = BotConfig.query.first()
    lava_cfg = LavalinkConfig.query.first()
    panel_cfg = PanelConfig.query.first()
    env_vars = EnvVariable.query.order_by(EnvVariable.key).all()
    return render_template("settings.html", bot_cfg=bot_cfg, lava_cfg=lava_cfg,
                           panel_cfg=panel_cfg, env_vars=env_vars)


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
    if "client_id" in data:
        cfg.client_id = data["client_id"][:30]
    if "client_secret" in data and data["client_secret"]:
        cfg.client_secret = data["client_secret"]
    if "prefix" in data:
        cfg.prefix = data["prefix"][:10]
    if "timezone" in data:
        cfg.timezone = data["timezone"][:50]
    if "description" in data:
        cfg.description = data["description"][:200]
    if "status_type" in data:
        cfg.status_type = data["status_type"]
    if "activity_type" in data:
        cfg.activity_type = data["activity_type"]
    if "activity_text" in data:
        cfg.activity_text = data["activity_text"][:128]
    if "intent_members" in data:
        cfg.intent_members = bool(data["intent_members"])
    if "intent_message_content" in data:
        cfg.intent_message_content = bool(data["intent_message_content"])

    db.session.commit()

    # Inyectar en el proceso actual para efecto inmediato
    if cfg.token:        os.environ["BOT_TOKEN"] = cfg.token
    if cfg.client_id:    os.environ["DISCORD_CLIENT_ID"] = cfg.client_id
    if cfg.client_secret: os.environ["DISCORD_CLIENT_SECRET"] = cfg.client_secret
    if cfg.prefix:       os.environ["BOT_PREFIX"] = cfg.prefix

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
    """Reinicia el bot para que el cog Lavalink reconecte con la nueva config."""
    from services import bot_manager
    status = bot_manager.get_status()
    if not status["running"]:
        return jsonify({"success": False, "message": "El bot no está corriendo."})

    # Inyectar config en env para que main.py la lea al reiniciar
    cfg = LavalinkConfig.query.first()
    if cfg:
        os.environ["LAVALINK_HOST"]     = cfg.host or ""
        os.environ["LAVALINK_PORT"]     = str(cfg.port or 2333)
        os.environ["LAVALINK_PASSWORD"] = cfg.password or "youshallnotpass"

    import threading
    def _restart():
        import time
        time.sleep(0.5)
        bot_manager.restart_bot()
    threading.Thread(target=_restart, daemon=True).start()

    logger.info("Reconexión Lavalink: bot reiniciando.")
    return jsonify({"success": True, "message": "Bot reiniciando para aplicar nueva config Lavalink…"})


@settings_bp.route("/api/settings/vars", methods=["GET"])
@login_required
def list_vars():
    """Lista todas las variables (valores secretos ocultos)."""
    vars_ = EnvVariable.query.order_by(EnvVariable.key).all()
    return jsonify({"vars": [v.to_dict() for v in vars_]})


@settings_bp.route("/api/settings/vars", methods=["POST"])
@login_required
def save_var():
    """Crea o actualiza una variable. Si is_secret=True el valor se oculta en la UI."""
    data = request.get_json(silent=True) or {}
    key = (data.get("key") or "").strip().upper().replace(" ", "_")
    value = data.get("value", "")
    is_secret = bool(data.get("is_secret", False))
    description = (data.get("description") or "")[:200]

    if not key:
        return jsonify({"success": False, "message": "La clave no puede estar vacía."}), 400
    if not key.replace("_", "").isalnum():
        return jsonify({"success": False, "message": "Clave inválida. Usa solo letras, números y guiones bajos."}), 400

    var = EnvVariable.query.filter_by(key=key).first()
    if var:
        # Si el valor viene vacío en una variable secreta, no sobreescribir
        if not (is_secret and value == ""):
            var.value = value
        var.is_secret = is_secret
        var.description = description
    else:
        var = EnvVariable(key=key, value=value, is_secret=is_secret, description=description)
        db.session.add(var)

    db.session.commit()
    # Inyectar en el proceso actual para uso inmediato
    os.environ[key] = var.value
    logger.info(f"Variable de entorno guardada: {key}")
    return jsonify({"success": True, "message": f"Variable '{key}' guardada.", "var": var.to_dict()})


@settings_bp.route("/api/settings/vars/reveal/<int:var_id>", methods=["GET"])
@login_required
def reveal_var(var_id):
    """Devuelve el valor real de una variable (incluso secretas)."""
    var = db.session.get(EnvVariable, var_id)
    if not var:
        return jsonify({"success": False}), 404
    return jsonify({"value": var.value})


@settings_bp.route("/api/settings/vars/<int:var_id>", methods=["DELETE"])
@login_required
def delete_var(var_id):
    var = db.session.get(EnvVariable, var_id)
    if not var:
        return jsonify({"success": False, "message": "Variable no encontrada."}), 404
    key = var.key
    db.session.delete(var)
    db.session.commit()
    os.environ.pop(key, None)
    logger.info(f"Variable de entorno eliminada: {key}")
    return jsonify({"success": True, "message": f"Variable '{key}' eliminada."})


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
