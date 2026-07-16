"""Modelo de configuración Lavalink."""
from datetime import datetime, timezone
from database.db import db


class LavalinkConfig(db.Model):
    __tablename__ = "lavalink_config"

    id = db.Column(db.Integer, primary_key=True)
    host = db.Column(db.String(255), default="localhost")
    port = db.Column(db.Integer, default=2333)
    password = db.Column(db.Text, default="youshallnotpass")
    ssl = db.Column(db.Boolean, default=False)
    updated_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    def to_dict(self):
        return {
            "id": self.id,
            "host": self.host,
            "port": self.port,
            "ssl": self.ssl,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            # password no se expone en API pública
        }
