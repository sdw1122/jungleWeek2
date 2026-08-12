from __future__ import annotations

from datetime import datetime

from sqlalchemy import CheckConstraint, func

from ..extensions import db


class PlantSpecies(db.Model):
    __tablename__ = "plant_species"

    id = db.Column(
        db.BigInteger().with_variant(db.Integer, "sqlite"),
        primary_key=True,
    )
    name = db.Column(db.String(50), nullable=False, unique=True)
    category = db.Column(db.String(30))
    emoji = db.Column(db.String(16))
    image_url = db.Column(db.Text)
    created_at = db.Column(
        db.DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )


class Plant(db.Model):
    __tablename__ = "plants"
    __table_args__ = (
        CheckConstraint(
            "growth_score BETWEEN 0 AND 100", name="chk_plants_growth_score"
        ),
        CheckConstraint(
            "positive_energy >= 0", name="chk_plants_positive_energy"
        ),
        CheckConstraint(
            "negative_energy >= 0", name="chk_plants_negative_energy"
        ),
        CheckConstraint(
            "status IN ('GROWING', 'GIFT_READY', 'GIFTED')",
            name="chk_plants_status",
        ),
    )

    id = db.Column(
        db.BigInteger().with_variant(db.Integer, "sqlite"),
        primary_key=True,
    )
    species_id = db.Column(
        db.BigInteger().with_variant(db.Integer, "sqlite"),
        db.ForeignKey("plant_species.id", ondelete="RESTRICT"),
        nullable=False,
    )
    name = db.Column(db.String(50), nullable=False)
    growth_score = db.Column(db.SmallInteger, nullable=False, default=0)
    positive_energy = db.Column(db.Integer, nullable=False, default=0)
    negative_energy = db.Column(db.Integer, nullable=False, default=0)
    mood = db.Column(db.String(30))
    status = db.Column(db.String(20), nullable=False, default="GROWING")
    adopted_at = db.Column(
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

    species = db.relationship(PlantSpecies, lazy="joined")

    @property
    def growth_stage(self) -> str:
        if self.growth_score >= 70:
            return "FLOWER"
        if self.growth_score >= 40:
            return "BUD"
        if self.growth_score >= 20:
            return "TRUE_LEAF"
        if self.growth_score >= 5:
            return "COTYLEDON"
        return "SEED"

    def to_dict(self, ownership: PlantOwnership | None = None) -> dict:
        stage_labels = {
            "SEED": "씨앗",
            "COTYLEDON": "떡잎",
            "TRUE_LEAF": "본잎",
            "BUD": "봉오리",
            "FLOWER": "꽃",
        }
        return {
            "id": self.id,
            "name": self.name,
            "speciesName": self.species.name if self.species else None,
            "category": self.species.category if self.species else None,
            "emoji": self.species.emoji if self.species else None,
            "imageUrl": self.species.image_url if self.species else None,
            "growthScore": self.growth_score,
            "positiveEnergy": self.positive_energy,
            "negativeEnergy": self.negative_energy,
            "growthStage": self.growth_stage,
            "stageLabel": stage_labels[self.growth_stage],
            "mood": self.mood,
            "status": self.status,
            "adoptedAt": _isoformat(self.adopted_at),
            "ownershipStartedAt": _isoformat(ownership.started_at)
            if ownership
            else None,
        }


class PlantOwnership(db.Model):
    __tablename__ = "plant_ownerships"
    __table_args__ = (
        CheckConstraint(
            "acquisition_type IN ('ADOPTION', 'GIFT')",
            name="chk_plant_ownerships_acquisition_type",
        ),
        CheckConstraint(
            "(acquisition_type = 'ADOPTION' AND gift_id IS NULL) OR "
            "(acquisition_type = 'GIFT' AND gift_id IS NOT NULL)",
            name="chk_plant_ownerships_gift",
        ),
        CheckConstraint(
            "ended_at IS NULL OR ended_at >= started_at",
            name="chk_plant_ownerships_period",
        ),
    )

    id = db.Column(
        db.BigInteger().with_variant(db.Integer, "sqlite"),
        primary_key=True,
    )
    plant_id = db.Column(
        db.BigInteger().with_variant(db.Integer, "sqlite"),
        db.ForeignKey("plants.id", ondelete="RESTRICT"),
        nullable=False,
    )
    owner_user_id = db.Column(
        db.BigInteger().with_variant(db.Integer, "sqlite"),
        db.ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
    )
    acquisition_type = db.Column(db.String(20), nullable=False)
    gift_id = db.Column(
        db.BigInteger().with_variant(db.Integer, "sqlite"),
        db.ForeignKey("gifts.id", ondelete="RESTRICT"),
    )
    started_at = db.Column(
        db.DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    ended_at = db.Column(db.DateTime(timezone=True))

    plant = db.relationship(Plant)
    gift = db.relationship("Gift", foreign_keys=[gift_id])


class CareLog(db.Model):
    __tablename__ = "care_logs"
    __table_args__ = (
        CheckConstraint(
            "action_type IN ('PET', 'WATER', 'SUNLIGHT', 'IGNORE')",
            name="chk_care_logs_action_type",
        ),
    )

    id = db.Column(
        db.BigInteger().with_variant(db.Integer, "sqlite"),
        primary_key=True,
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
    action_type = db.Column(db.String(30), nullable=False)
    growth_delta = db.Column(db.SmallInteger, nullable=False, default=0)
    positive_delta = db.Column(db.Integer, nullable=False, default=0)
    negative_delta = db.Column(db.Integer, nullable=False, default=0)
    note = db.Column(db.Text)
    created_at = db.Column(
        db.DateTime(timezone=True), nullable=False, server_default=func.now()
    )


def _isoformat(value: datetime | None) -> str | None:
    return value.isoformat() if value else None
