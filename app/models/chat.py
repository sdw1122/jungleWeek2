from __future__ import annotations

from sqlalchemy import CheckConstraint, func

from ..extensions import db


class ChatSession(db.Model):
    __tablename__ = "chat_sessions"
    __table_args__ = (
        CheckConstraint(
            "ended_at IS NULL OR ended_at >= started_at",
            name="chk_chat_sessions_period",
        ),
    )

    id = db.Column(
        db.BigInteger().with_variant(db.Integer, "sqlite"), primary_key=True
    )
    plant_id = db.Column(
        db.BigInteger().with_variant(db.Integer, "sqlite"),
        db.ForeignKey("plants.id", ondelete="RESTRICT"),
        nullable=False,
    )
    user_id = db.Column(
        db.BigInteger().with_variant(db.Integer, "sqlite"),
        db.ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
    )
    started_at = db.Column(
        db.DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    ended_at = db.Column(db.DateTime(timezone=True))


class ChatMessage(db.Model):
    __tablename__ = "chat_messages"
    __table_args__ = (
        CheckConstraint(
            "role IN ('USER', 'PLANT', 'SYSTEM')",
            name="chk_chat_messages_role",
        ),
    )

    id = db.Column(
        db.BigInteger().with_variant(db.Integer, "sqlite"), primary_key=True
    )
    session_id = db.Column(
        db.BigInteger().with_variant(db.Integer, "sqlite"),
        db.ForeignKey("chat_sessions.id", ondelete="CASCADE"),
        nullable=False,
    )
    role = db.Column(db.String(20), nullable=False)
    content = db.Column(db.Text, nullable=False)
    positive_delta = db.Column(db.Integer, nullable=False, default=0)
    negative_delta = db.Column(db.Integer, nullable=False, default=0)
    created_at = db.Column(
        db.DateTime(timezone=True), nullable=False, server_default=func.now()
    )
