"""
Configuración central del panel.
Todas las variables sensibles se leen desde el entorno (.env).
"""
import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    # Flask
    SECRET_KEY: str = os.environ.get("SECRET_KEY", "dev-secret-change-me")
    SESSION_KEY: str = os.environ.get("SESSION_KEY", "dev-session-change-me")
    FLASK_ENV: str = os.environ.get("FLASK_ENV", "production")
    DEBUG: bool = FLASK_ENV == "development"
    # PORT: Render usa "PORT", Replit usa "PANEL_PORT", fallback 5000
    PORT: int = int(os.environ.get("PORT") or os.environ.get("PANEL_PORT", 5000))

    # SQLAlchemy / Neon PostgreSQL
    # NEON_DATABASE_URL takes priority so it doesn't conflict with Replit's managed DATABASE_URL
    SQLALCHEMY_DATABASE_URI: str = (
        os.environ.get("NEON_DATABASE_URL") or os.environ.get("DATABASE_URL", "")
    )
    SQLALCHEMY_TRACK_MODIFICATIONS: bool = False
    SQLALCHEMY_ENGINE_OPTIONS: dict = {
        "pool_pre_ping": True,
        "pool_recycle": 300,
        "pool_size": 5,
        "max_overflow": 10,
    }

    # WTF / CSRF
    WTF_CSRF_ENABLED: bool = True
    WTF_CSRF_TIME_LIMIT: int = 3600

    # Sesiones
    SESSION_COOKIE_HTTPONLY: bool = True
    SESSION_COOKIE_SAMESITE: str = "None"   # Necesario para el proxy/iframe de Replit
    SESSION_COOKIE_SECURE: bool = True       # Requerido cuando SameSite=None
    PERMANENT_SESSION_LIFETIME: int = 86400  # 24h

    # Bot Discord
    BOT_TOKEN: str = os.environ.get("BOT_TOKEN", "")
    BOT_PREFIX: str = os.environ.get("BOT_PREFIX", "!")
    BOT_TIMEZONE: str = os.environ.get("BOT_TIMEZONE", "UTC")

    # Cloudflare R2
    R2_ENDPOINT: str = os.environ.get("R2_ENDPOINT", "")
    R2_ACCESS_KEY: str = os.environ.get("R2_ACCESS_KEY", "")
    R2_SECRET_KEY: str = os.environ.get("R2_SECRET_KEY", "")
    R2_BUCKET: str = os.environ.get("R2_BUCKET", "")
    R2_PUBLIC_URL: str = os.environ.get("R2_PUBLIC_URL", "")

    # Lavalink
    LAVALINK_HOST: str = os.environ.get("LAVALINK_HOST", "localhost")
    LAVALINK_PORT: int = int(os.environ.get("LAVALINK_PORT", 2333))
    LAVALINK_PASSWORD: str = os.environ.get("LAVALINK_PASSWORD", "youshallnotpass")
    LAVALINK_SSL: bool = os.environ.get("LAVALINK_SSL", "false").lower() == "true"

    # Rutas del sistema
    BASE_DIR: str = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    UPLOADS_DIR: str = os.path.join(BASE_DIR, "uploads")
    BACKUPS_DIR: str = os.path.join(BASE_DIR, "backups")
    LOGS_DIR: str = os.path.join(BASE_DIR, "logs")
    BOT_DIR: str = os.path.join(BASE_DIR, "bot_files")

    # Admin inicial
    ADMIN_USERNAME: str = os.environ.get("ADMIN_USERNAME", "admin")
    ADMIN_PASSWORD: str = os.environ.get("ADMIN_PASSWORD", "changeme123")

    @classmethod
    def validate(cls) -> list[str]:
        """Retorna lista de variables críticas faltantes."""
        missing = []
        if not cls.DATABASE_URL:
            missing.append("DATABASE_URL")
        if not cls.SECRET_KEY or cls.SECRET_KEY == "dev-secret-change-me":
            missing.append("SECRET_KEY (usando valor por defecto inseguro)")
        return missing
