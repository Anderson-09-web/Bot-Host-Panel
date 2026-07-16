"""Modelo de configuración del panel web."""
from datetime import datetime, timezone
from database.db import db


class PanelConfig(db.Model):
    __tablename__ = "panel_config"

    id = db.Column(db.Integer, primary_key=True)
    panel_name = db.Column(db.String(100), default="Discord Bot Panel")
    theme = db.Column(db.String(20), default="dark")
    updated_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    def to_dict(self):
        return {
            "id": self.id,
            "panel_name": self.panel_name,
            "theme": self.theme,
        }
