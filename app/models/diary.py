from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import CheckConstraint, JSON, UniqueConstraint, func, text
from sqlalchemy.dialects.postgresql import JSONB

from ..extensions import db


class DiaryEntry(db.Model):
    __tablename__ = "diary_entries"
    __table_args__ = (
        CheckConstraint(
            "source_type IN ('USER', 'AI')",
            name="chk_diary_entries_source_type",
        ),
        CheckConstraint(
            "growth_score_snapshot BETWEEN 0 AND 100",
            name="chk_diary_growth_score",
        ),
        CheckConstraint(
            "positive_energy_snapshot >= 0",
            name="chk_diary_positive_energy",
        ),
        CheckConstraint(
            "negative_energy_snapshot >= 0",
            name="chk_diary_negative_energy",
        ),
        CheckConstraint(
            "growth_stage_snapshot IN "
            "('SEED', 'COTYLEDON', 'TRUE_LEAF', 'BUD', 'FLOWER')",
            name="chk_diary_growth_stage",
        ),
        CheckConstraint(
            "growth_tendency_snapshot IN ('POSITIVE', 'NEGATIVE')",
            name="chk_diary_growth_tendency",
        ),
        UniqueConstraint("plant_id", "diary_date", name="uq_diary_plant_date"),
    )

    id = db.Column(
        db.BigInteger().with_variant(db.Integer, "sqlite"), primary_key=True
    )
    plant_id = db.Column(
        db.BigInteger().with_variant(db.Integer, "sqlite"),
        db.ForeignKey("plants.id", ondelete="RESTRICT"),
        nullable=False,
    )
    author_user_id = db.Column(
        db.BigInteger().with_variant(db.Integer, "sqlite"),
        db.ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
    )
    title = db.Column(db.String(150))
    content = db.Column(db.Text, nullable=False)
    source_type = db.Column(db.String(20), nullable=False)
    mood_snapshot = db.Column(db.String(30))
    growth_score_snapshot = db.Column(db.SmallInteger, nullable=False)
    positive_energy_snapshot = db.Column(db.Integer, nullable=False)
    negative_energy_snapshot = db.Column(db.Integer, nullable=False)
    growth_stage_snapshot = db.Column(db.String(20), nullable=False)
    growth_tendency_snapshot = db.Column(db.String(20), nullable=False)
    diary_date = db.Column(db.Date, nullable=False)
    activity_summary = db.Column(
        JSON().with_variant(JSONB, "postgresql"),
        nullable=False,
        default=dict,
        server_default=text("'{}'"),
    )
    diary_at = db.Column(
        db.DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    created_at = db.Column(
        db.DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    plant = db.relationship("Plant", foreign_keys=[plant_id])
    author = db.relationship("User", foreign_keys=[author_user_id])

    def to_dict(self, *, can_edit: bool = False, include_content: bool = True) -> dict:
        data = {
            "id": self.id,
            "plantId": self.plant_id,
            "author": {
                "id": self.author.id,
                "nickname": self.author.nickname,
            }
            if self.author
            else None,
            "title": self.title,
            "sourceType": self.source_type,
            "mood": self.mood_snapshot,
            "growthScore": self.growth_score_snapshot,
            "positiveEnergy": self.positive_energy_snapshot,
            "negativeEnergy": self.negative_energy_snapshot,
            "growthStage": self.growth_stage_snapshot,
            "growthTendency": self.growth_tendency_snapshot,
            "activitySummary": self.activity_summary or {},
            "diaryDate": self.diary_date.isoformat() if self.diary_date else None,
            "diaryAt": _isoformat(self.diary_at),
            "createdAt": _isoformat(self.created_at),
            "updatedAt": _isoformat(self.updated_at),
            "canEdit": can_edit,
        }
        if include_content:
            data["content"] = self.content
        else:
            data["preview"] = _preview(self.content)
        return data


def _isoformat(value: datetime | None) -> str | None:
    return value.isoformat() if value else None


def _preview(content: str, maximum: int = 120) -> str:
    normalized = " ".join((content or "").split())
    return normalized if len(normalized) <= maximum else f"{normalized[:maximum - 1]}…"
