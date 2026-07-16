"""Página de Variables de Entorno."""
import os
import logging
from flask import Blueprint, render_template, jsonify, request
from flask_login import login_required
from database.db import db
from models.env_variable import EnvVariable

variables_bp = Blueprint("variables", __name__)
logger = logging.getLogger("variables")


@variables_bp.route("/variables")
@login_required
def index():
    env_vars = EnvVariable.query.order_by(EnvVariable.key).all()
    return render_template("variables.html", env_vars=env_vars)


@variables_bp.route("/api/variables", methods=["GET"])
@login_required
def list_vars():
    vars_ = EnvVariable.query.order_by(EnvVariable.key).all()
    return jsonify({"vars": [v.to_dict() for v in vars_]})


@variables_bp.route("/api/variables", methods=["POST"])
@login_required
def save_var():
    data = request.get_json(silent=True) or {}
    key = (data.get("key") or "").strip().upper().replace(" ", "_")
    value = data.get("value", "")
    is_secret = bool(data.get("is_secret", False))
    description = (data.get("description") or "")[:200]

    if not key:
        return jsonify({"success": False, "message": "La clave no puede estar vacía."}), 400
    if not key.replace("_", "").isalnum():
        return jsonify({"success": False, "message": "Solo letras, números y guiones bajos."}), 400

    var = EnvVariable.query.filter_by(key=key).first()
    if var:
        if not (is_secret and value == ""):
            var.value = value
        var.is_secret = is_secret
        var.description = description
    else:
        var = EnvVariable(key=key, value=value, is_secret=is_secret, description=description)
        db.session.add(var)

    db.session.commit()
    os.environ[key] = var.value
    logger.info(f"Variable guardada: {key}")
    return jsonify({"success": True, "message": f"Variable '{key}' guardada.", "var": var.to_dict()})


@variables_bp.route("/api/variables/reveal/<int:var_id>", methods=["GET"])
@login_required
def reveal_var(var_id):
    var = db.session.get(EnvVariable, var_id)
    if not var:
        return jsonify({"success": False}), 404
    return jsonify({"value": var.value})


@variables_bp.route("/api/variables/<int:var_id>", methods=["DELETE"])
@login_required
def delete_var(var_id):
    var = db.session.get(EnvVariable, var_id)
    if not var:
        return jsonify({"success": False, "message": "No encontrada."}), 404
    key = var.key
    db.session.delete(var)
    db.session.commit()
    os.environ.pop(key, None)
    logger.info(f"Variable eliminada: {key}")
    return jsonify({"success": True, "message": f"Variable '{key}' eliminada."})
