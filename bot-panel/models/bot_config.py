"""Modelo de configuración del bot Discord."""
from datetime import datetime, timezone
from database.db import db


class BotConfig(db.Model):
    __tablename__ = "bot_config"

    id = db.Column(db.Integer, primary_key=True)
    token = db.Column(db.Text, nullable=True, default="")
    prefix = db.Column(db.String(10), default="!")
    timezone = db.Column(db.String(50), default="UTC")
    updated_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    def to_dict(self):
        return {
            "id": self.id,
            "prefix": self.prefix,
            "timezone": self.timezone,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            # token nunca se expone en el dict público
        }
