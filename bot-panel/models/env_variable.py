"""Modelo para variables de entorno gestionadas desde el panel."""
from datetime import datetime, timezone
from database.db import db


class EnvVariable(db.Model):
    __tablename__ = "env_variables"

    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(100), unique=True, nullable=False)
    value = db.Column(db.Text, nullable=False, default="")
    is_secret = db.Column(db.Boolean, default=False)   # oculta el valor en la UI
    description = db.Column(db.String(200), default="")
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc),
                           onupdate=lambda: datetime.now(timezone.utc))

    def to_dict(self, reveal: bool = False) -> dict:
        return {
            "id": self.id,
            "key": self.key,
            "value": self.value if (reveal or not self.is_secret) else "••••••••",
            "is_secret": self.is_secret,
            "description": self.description,
            "updated_at": self.updated_at.strftime("%Y-%m-%d %H:%M") if self.updated_at else "",
        }
