"""
Conexión central a Neon PostgreSQL usando SQLAlchemy + Flask-SQLAlchemy.
"""
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


db = SQLAlchemy(model_class=Base)


def init_db(app):
    """Inicializa la base de datos con la app Flask."""
    db.init_app(app)
    with app.app_context():
        # Importar todos los modelos antes de crear tablas
        from models import user, bot_config, log_entry, lavalink_config, panel_config  # noqa: F401
        db.create_all()
        _seed_defaults(app)


def _seed_defaults(app):
    """Crea registros iniciales si no existen."""
    from models.user import User
    from models.bot_config import BotConfig
    from models.lavalink_config import LavalinkConfig
    from models.panel_config import PanelConfig
    from config.settings import Config
    import werkzeug.security as ws

    # Usuario admin
    if not User.query.filter_by(username=Config.ADMIN_USERNAME).first():
        admin = User(
            username=Config.ADMIN_USERNAME,
            password_hash=ws.generate_password_hash(Config.ADMIN_PASSWORD),
            is_admin=True,
        )
        db.session.add(admin)

    # Configuración del bot
    if not BotConfig.query.first():
        bot_cfg = BotConfig(
            token=Config.BOT_TOKEN,
            prefix=Config.BOT_PREFIX,
            timezone=Config.BOT_TIMEZONE,
        )
        db.session.add(bot_cfg)

    # Configuración Lavalink
    if not LavalinkConfig.query.first():
        lava_cfg = LavalinkConfig(
            host=Config.LAVALINK_HOST,
            port=Config.LAVALINK_PORT,
            password=Config.LAVALINK_PASSWORD,
            ssl=Config.LAVALINK_SSL,
        )
        db.session.add(lava_cfg)

    # Configuración del panel
    if not PanelConfig.query.first():
        panel_cfg = PanelConfig(panel_name="Discord Bot Panel", theme="dark")
        db.session.add(panel_cfg)

    db.session.commit()
