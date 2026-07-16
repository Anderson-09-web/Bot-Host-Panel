"""Rutas de autenticación: login y logout."""
import logging
from datetime import datetime, timezone
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField
from wtforms.validators import DataRequired, Length
from werkzeug.security import check_password_hash
from database.db import db
from models.user import User

auth_bp = Blueprint("auth", __name__)
logger = logging.getLogger("auth")


class LoginForm(FlaskForm):
    username = StringField("Usuario", validators=[DataRequired(), Length(1, 80)])
    password = PasswordField("Contraseña", validators=[DataRequired()])
    remember = BooleanField("Recordarme")


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard.index"))

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and check_password_hash(user.password_hash, form.password.data):
            login_user(user, remember=form.remember.data)
            user.last_login = datetime.now(timezone.utc)
            db.session.commit()
            logger.info(f"Login exitoso: {user.username}")
            next_page = request.args.get("next")
            return redirect(next_page or url_for("dashboard.index"))
        flash("Usuario o contraseña incorrectos.", "error")
        logger.warning(f"Login fallido para: {form.username.data}")

    return render_template("login.html", form=form)


@auth_bp.route("/logout")
@login_required
def logout():
    logger.info(f"Logout: {current_user.username}")
    logout_user()
    flash("Sesión cerrada correctamente.", "info")
    return redirect(url_for("auth.login"))
