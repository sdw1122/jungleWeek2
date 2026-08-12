from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import CheckConstraint, func

from ..extensions import db


class Gift(db.Model):
    __tablename__ = "gifts"
    __table_args__ = (
        CheckConstraint(
            "status IN ('READY', 'SENT', 'ACCEPTED', 'CANCELLED')",
            name="chk_gifts_status",
        ),
        CheckConstraint(
            "(status = 'ACCEPTED' AND accepted_at IS NOT NULL) OR "
            "(status <> 'ACCEPTED' AND accepted_at IS NULL)",
            name="chk_gifts_acceptance",
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
    sender_user_id = db.Column(
        db.BigInteger().with_variant(db.Integer, "sqlite"),
        db.ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
    )
    recipient_user_id = db.Column(
        db.BigInteger().with_variant(db.Integer, "sqlite"),
        db.ForeignKey("users.id", ondelete="SET NULL"),
    )
    recipient_name = db.Column(db.String(50), nullable=False)
    gifted_on = db.Column(db.Date, nullable=False)
    message_card = db.Column(db.Text)
    status = db.Column(db.String(20), nullable=False, default="READY")
    accepted_at = db.Column(db.DateTime(timezone=True))
    recipient_viewed_at = db.Column(db.DateTime(timezone=True))
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
    sender = db.relationship("User", foreign_keys=[sender_user_id])
    recipient = db.relationship("User", foreign_keys=[recipient_user_id])

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "plantId": self.plant_id,
            "sender": {
                "id": self.sender.id,
                "nickname": self.sender.nickname,
            }
            if self.sender
            else None,
            "recipient": {
                "id": self.recipient.id,
                "nickname": self.recipient.nickname,
            }
            if self.recipient
            else None,
            "recipientName": self.recipient_name,
            "giftedOn": _isoformat(self.gifted_on),
            "message": self.message_card,
            "status": self.status,
            "acceptedAt": _isoformat(self.accepted_at),
            "recipientViewedAt": _isoformat(self.recipient_viewed_at),
            "createdAt": _isoformat(self.created_at),
        }


def _isoformat(value: date | datetime | None) -> str | None:
    return value.isoformat() if value else None
