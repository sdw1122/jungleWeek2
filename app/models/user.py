from __future__ import annotations

from datetime import datetime

from flask_login import UserMixin
from sqlalchemy import CheckConstraint, func
from werkzeug.security import check_password_hash, generate_password_hash

from ..extensions import db


class User(UserMixin, db.Model):
    __tablename__ = "users"
    __table_args__ = (
        CheckConstraint(
            "auth_provider IN ('LOCAL', 'GOOGLE')",
            name="chk_users_auth_provider",
        ),
        CheckConstraint(
            "(auth_provider = 'LOCAL' AND password_hash IS NOT NULL "
            "AND google_subject IS NULL) OR "
            "(auth_provider = 'GOOGLE' AND google_subject IS NOT NULL)",
            name="chk_users_auth_credentials",
        ),
        CheckConstraint(
            "status IN ('ACTIVE', 'WITHDRAWN')",
            name="chk_users_status",
        ),
    )

    id = db.Column(
        db.BigInteger().with_variant(db.Integer, "sqlite"),
        primary_key=True,
    )
    email = db.Column(db.String(255), nullable=False, unique=True)
    password_hash = db.Column(db.String(255))
    auth_provider = db.Column(db.String(20), nullable=False, default="LOCAL")
    google_subject = db.Column(db.String(255), unique=True)
    nickname = db.Column(db.String(50), nullable=False, unique=True)
    profile_image_url = db.Column(db.Text)
    status = db.Column(db.String(20), nullable=False, default="ACTIVE")
    created_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    updated_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    @property
    def is_active(self) -> bool:
        return self.status == "ACTIVE"

    def set_password(self, password: str) -> None:
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        if not self.password_hash:
            return False
        return check_password_hash(self.password_hash, password)

    def to_dict(self) -> dict[str, str | int | None]:
        return {
            "id": self.id,
            "email": self.email,
            "nickname": self.nickname,
            "authProvider": self.auth_provider,
            "profileImageUrl": self.profile_image_url,
            "status": self.status,
            "createdAt": self._isoformat(self.created_at),
        }

    @staticmethod
    def _isoformat(value: datetime | None) -> str | None:
        return value.isoformat() if value else None
