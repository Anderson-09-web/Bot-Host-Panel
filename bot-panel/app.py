"""
Panel Web para Bot de Discord — Aplicación Flask principal.
Punto de entrada. Ejecutar con: python app.py
"""
import os
import logging
from flask import Flask, redirect, url_for
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect
from dotenv import load_dotenv

load_dotenv()

from config.settings import Config
from database.db import db, init_db
from services.log_service import setup_logging


def create_app() -> Flask:
    app = Flask(
        __name__,
        template_folder="templates",
        static_folder="static",
    )
    app.config.from_object(Config)

    # Asegurar directorios necesarios
    for d in [Config.UPLOADS_DIR, Config.BACKUPS_DIR, Config.LOGS_DIR,
              os.path.join(Config.BASE_DIR, "bot_files"),
              os.path.join(Config.BASE_DIR, "instance")]:
        os.makedirs(d, exist_ok=True)

    # Logging
    setup_logging(app)
    logger = logging.getLogger("app")

    # DB
    if not Config.SQLALCHEMY_DATABASE_URI:
        logger.warning("DATABASE_URL no configurada. Usando SQLite temporal.")
        app.config["SQLALCHEMY_DATABASE_URI"] = (
            f"sqlite:///{os.path.join(Config.BASE_DIR, 'instance', 'panel.db')}"
        )

    init_db(app)

    # CSRF
    CSRFProtect(app)

    # Flask-Login
    login_manager = LoginManager(app)
    login_manager.login_view = "auth.login"
    login_manager.login_message = "Inicia sesión para continuar."
    login_manager.login_message_category = "warning"

    from models.user import User

    @login_manager.user_loader
    def load_user(user_id: str):
        return db.session.get(User, int(user_id))

    # Blueprints
    from routes.auth import auth_bp
    from routes.dashboard import dashboard_bp
    from routes.console import console_bp
    from routes.settings import settings_bp
    from routes.files import files_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(console_bp)
    app.register_blueprint(settings_bp)
    app.register_blueprint(files_bp)

    @app.route("/")
    def root():
        return redirect(url_for("dashboard.index"))

    @app.errorhandler(404)
    def not_found(e):
        from flask import render_template
        return render_template("error.html", code=404, message="Página no encontrada"), 404

    @app.errorhandler(500)
    def server_error(e):
        from flask import render_template
        return render_template("error.html", code=500, message="Error interno del servidor"), 500

    logger.info(f"Panel iniciado — http://0.0.0.0:{Config.PORT}")
    return app


app = create_app()

if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=Config.PORT,
        debug=Config.DEBUG,
        use_reloader=False,
    )
