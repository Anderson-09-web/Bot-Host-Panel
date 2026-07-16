"""Modelo de configuración del bot Discord."""
from datetime import datetime, timezone
from database.db import db


class BotConfig(db.Model):
    __tablename__ = "bot_config"

    id             = db.Column(db.Integer, primary_key=True)
    token          = db.Column(db.Text, nullable=True, default="")
    client_id      = db.Column(db.String(30), default="")      # Application ID de Discord
    client_secret  = db.Column(db.Text, default="")            # Client Secret (OAuth2)
    prefix         = db.Column(db.String(10), default="!")
    timezone       = db.Column(db.String(50), default="UTC")
    description    = db.Column(db.String(200), default="")     # Descripción del bot
    # Presencia / Activity
    status_type    = db.Column(db.String(20), default="online")   # online/idle/dnd/invisible
    activity_type  = db.Column(db.String(20), default="playing")  # playing/watching/listening/streaming/competing
    activity_text  = db.Column(db.String(128), default="")
    # Intents
    intent_members = db.Column(db.Boolean, default=True)
    intent_message_content = db.Column(db.Boolean, default=True)

    updated_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    def to_dict(self):
        return {
            "id": self.id,
            "client_id": self.client_id,
            "prefix": self.prefix,
            "timezone": self.timezone,
            "description": self.description,
            "status_type": self.status_type,
            "activity_type": self.activity_type,
            "activity_text": self.activity_text,
            "intent_members": self.intent_members,
            "intent_message_content": self.intent_message_content,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
