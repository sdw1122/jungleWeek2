from __future__ import annotations

from datetime import datetime

from sqlalchemy import CheckConstraint, UniqueConstraint, func

from ..extensions import db


class GuestbookEntry(db.Model):
    __tablename__ = "public_guestbook_entries"

    id = db.Column(
        db.BigInteger().with_variant(db.Integer, "sqlite"), primary_key=True
    )
    author_user_id = db.Column(
        db.BigInteger().with_variant(db.Integer, "sqlite"),
        db.ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
    )
    nickname_snapshot = db.Column(db.String(50), nullable=False)
    content = db.Column(db.String(500), nullable=False)
    created_at = db.Column(
        db.DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    author = db.relationship("User", foreign_keys=[author_user_id])
    replies = db.relationship(
        "GuestbookReply",
        back_populates="entry",
        cascade="all, delete-orphan",
        order_by="GuestbookReply.created_at",
    )
    reactions = db.relationship(
        "GuestbookReaction",
        back_populates="entry",
        cascade="all, delete-orphan",
    )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "authorUserId": self.author_user_id,
            "author": self.nickname_snapshot,
            "nicknameSnapshot": self.nickname_snapshot,
            "content": self.content,
            "createdAt": _timestamp_ms(self.created_at),
            "updatedAt": _timestamp_ms(self.updated_at),
            "reactions": _reaction_dict(self.reactions),
            "replies": [reply.to_dict() for reply in self.replies],
        }


class GuestbookReply(db.Model):
    __tablename__ = "guestbook_replies"

    id = db.Column(
        db.BigInteger().with_variant(db.Integer, "sqlite"), primary_key=True
    )
    entry_id = db.Column(
        db.BigInteger().with_variant(db.Integer, "sqlite"),
        db.ForeignKey("public_guestbook_entries.id", ondelete="CASCADE"),
        nullable=False,
    )
    author_user_id = db.Column(
        db.BigInteger().with_variant(db.Integer, "sqlite"),
        db.ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
    )
    nickname_snapshot = db.Column(db.String(50), nullable=False)
    content = db.Column(db.String(500), nullable=False)
    created_at = db.Column(
        db.DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    entry = db.relationship(GuestbookEntry, back_populates="replies")
    author = db.relationship("User", foreign_keys=[author_user_id])
    reactions = db.relationship(
        "GuestbookReplyReaction",
        back_populates="reply",
        cascade="all, delete-orphan",
    )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "authorUserId": self.author_user_id,
            "author": self.nickname_snapshot,
            "content": self.content,
            "createdAt": _timestamp_ms(self.created_at),
            "reactions": _reaction_dict(self.reactions),
        }


class GuestbookReaction(db.Model):
    __tablename__ = "guestbook_reactions"
    __table_args__ = (
        CheckConstraint(
            "reaction_type IN ('like', 'dislike')",
            name="chk_guestbook_reactions_type",
        ),
        UniqueConstraint(
            "entry_id", "user_id", name="uq_guestbook_entry_reaction_user"
        ),
    )

    id = db.Column(
        db.BigInteger().with_variant(db.Integer, "sqlite"), primary_key=True
    )
    entry_id = db.Column(
        db.BigInteger().with_variant(db.Integer, "sqlite"),
        db.ForeignKey("public_guestbook_entries.id", ondelete="CASCADE"),
        nullable=False,
    )
    user_id = db.Column(
        db.BigInteger().with_variant(db.Integer, "sqlite"),
        db.ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    reaction_type = db.Column(db.String(10), nullable=False)

    entry = db.relationship(GuestbookEntry, back_populates="reactions")
    user = db.relationship("User")


class GuestbookReplyReaction(db.Model):
    __tablename__ = "guestbook_reply_reactions"
    __table_args__ = (
        CheckConstraint(
            "reaction_type IN ('like', 'dislike')",
            name="chk_guestbook_reply_reactions_type",
        ),
        UniqueConstraint(
            "reply_id", "user_id", name="uq_guestbook_reply_reaction_user"
        ),
    )

    id = db.Column(
        db.BigInteger().with_variant(db.Integer, "sqlite"), primary_key=True
    )
    reply_id = db.Column(
        db.BigInteger().with_variant(db.Integer, "sqlite"),
        db.ForeignKey("guestbook_replies.id", ondelete="CASCADE"),
        nullable=False,
    )
    user_id = db.Column(
        db.BigInteger().with_variant(db.Integer, "sqlite"),
        db.ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    reaction_type = db.Column(db.String(10), nullable=False)

    reply = db.relationship(GuestbookReply, back_populates="reactions")
    user = db.relationship("User")


def _reaction_dict(reactions: list) -> dict:
    return {
        "likedBy": [r.user.nickname for r in reactions if r.reaction_type == "like"],
        "dislikedBy": [
            r.user.nickname for r in reactions if r.reaction_type == "dislike"
        ],
    }


def _timestamp_ms(value: datetime | None) -> int | None:
    return int(value.timestamp() * 1000) if value else None
