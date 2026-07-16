"""Modelo para logs del sistema."""
from datetime import datetime, timezone
from database.db import db


class LogEntry(db.Model):
    __tablename__ = "logs"

    id = db.Column(db.Integer, primary_key=True)
    level = db.Column(db.String(10), default="INFO")   # INFO, WARNING, ERROR, DEBUG
    source = db.Column(db.String(50), default="system")  # bot, panel, r2, lavalink
    message = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), index=True)

    def to_dict(self):
        return {
            "id": self.id,
            "level": self.level,
            "source": self.source,
            "message": self.message,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
