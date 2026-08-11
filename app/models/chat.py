from __future__ import annotations
from datetime import datetime
from sqlalchemy import func
from ..extensions import db

class ChatSession(db.Model):
    __tablename__ = 'chat_sessions'

    id = db.Column(db.BigInteger, primary_key=True)
    plant_id = db.Column(db.BigInteger, db.ForeignKey('plants.id', ondelete='RESTRICT'), nullable=False)
    user_id = db.Column(db.BigInteger, db.ForeignKey('users.id', ondelete='RESTRICT'), nullable=False)
    started_at = db.Column(db.DateTime(timezone=True), nullable=False, server_default=func.now())
    ended_at = db.Column(db.DateTime(timezone=True))

class ChatMessage(db.Model):
    __tablename__ = 'chat_messages'

    id = db.Column(db.BigInteger, primary_key=True)
    session_id = db.Column(db.BigInteger, db.ForeignKey('chat_sessions.id', ondelete='CASCADE'), nullable=False)
    role = db.Column(db.String(20), nullable=False)
    content = db.Column(db.Text, nullable=False)
    positive_delta = db.Column(db.Integer, nullable=False, default=0)
    negative_delta = db.Column(db.Integer, nullable=False, default=0)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, server_default=func.now())
