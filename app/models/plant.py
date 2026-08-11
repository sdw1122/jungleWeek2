from __future__ import annotations
from datetime import datetime
from sqlalchemy import func
from ..extensions import db

class Plant(db.Model):
    __tablename__ = 'plants'

    id = db.Column(db.BigInteger, primary_key=True)
    species_id = db.Column(db.BigInteger, nullable=False)
    name = db.Column(db.String(50), nullable=False)
    growth_score = db.Column(db.SmallInteger, nullable=False, default=0)
    positive_energy = db.Column(db.Integer, nullable=False, default=0)
    negative_energy = db.Column(db.Integer, nullable=False, default=0)
    status = db.Column(db.String(20), nullable=False, default='GROWING')
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = db.Column(db.DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())
