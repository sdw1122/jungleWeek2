from datetime import datetime, timezone

from ..extensions import db


class GuestbookEntry(db.Model):
    __tablename__ = "guestbook_entries"

    id = db.Column(db.Integer, primary_key=True)
    author_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    content = db.Column(db.String(500), nullable=False)
    created_at = db.Column(
        db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False
    )
    updated_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    author = db.relationship("User", backref=db.backref("guestbook_entries", lazy="dynamic"))
    replies = db.relationship("GuestbookReply", backref="entry", cascade="all, delete-orphan", order_by="GuestbookReply.created_at")
    reactions = db.relationship("GuestbookReaction", backref="entry", cascade="all, delete-orphan")

    def to_dict(self):
        liked_by = [r.user.nickname for r in self.reactions if r.reaction_type == "like"]
        disliked_by = [r.user.nickname for r in self.reactions if r.reaction_type == "dislike"]
        return {
            "id": self.id,
            "author": self.author.nickname,
            "content": self.content,
            "createdAt": int(self.created_at.timestamp() * 1000),
            "reactions": {
                "likedBy": liked_by,
                "dislikedBy": disliked_by
            },
            "replies": [reply.to_dict() for reply in self.replies]
        }


class GuestbookReply(db.Model):
    __tablename__ = "guestbook_replies"

    id = db.Column(db.Integer, primary_key=True)
    entry_id = db.Column(db.Integer, db.ForeignKey("guestbook_entries.id"), nullable=False)
    author_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    content = db.Column(db.String(500), nullable=False)
    created_at = db.Column(
        db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False
    )

    author = db.relationship("User", backref=db.backref("guestbook_replies", lazy="dynamic"))
    reactions = db.relationship("GuestbookReplyReaction", backref="reply", cascade="all, delete-orphan")

    def to_dict(self):
        liked_by = [r.user.nickname for r in self.reactions if r.reaction_type == "like"]
        disliked_by = [r.user.nickname for r in self.reactions if r.reaction_type == "dislike"]
        return {
            "id": self.id,
            "author": self.author.nickname,
            "content": self.content,
            "createdAt": int(self.created_at.timestamp() * 1000),
            "reactions": {
                "likedBy": liked_by,
                "dislikedBy": disliked_by
            }
        }


class GuestbookReaction(db.Model):
    __tablename__ = "guestbook_reactions"

    id = db.Column(db.Integer, primary_key=True)
    entry_id = db.Column(db.Integer, db.ForeignKey("guestbook_entries.id"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    reaction_type = db.Column(db.String(10), nullable=False)  # 'like' or 'dislike'

    user = db.relationship("User")


class GuestbookReplyReaction(db.Model):
    __tablename__ = "guestbook_reply_reactions"

    id = db.Column(db.Integer, primary_key=True)
    reply_id = db.Column(db.Integer, db.ForeignKey("guestbook_replies.id"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    reaction_type = db.Column(db.String(10), nullable=False)  # 'like' or 'dislike'

    user = db.relationship("User")
