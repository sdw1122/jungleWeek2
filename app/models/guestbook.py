from ..extensions import db
from datetime import datetime
import pytz

class GuestbookEntry(db.Model):
    __tablename__ = 'public_guestbook_entries'
    
    id = db.Column(db.BigInteger, primary_key=True)
    author_user_id = db.Column(db.BigInteger, db.ForeignKey('users.id', ondelete='RESTRICT'), nullable=False)
    nickname_snapshot = db.Column(db.String(50), nullable=False)
    content = db.Column(db.String(500), nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(pytz.utc), nullable=False)
    updated_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(pytz.utc), onupdate=lambda: datetime.now(pytz.utc), nullable=False)

    def to_dict(self):
        return {
            'id': self.id,
            'authorUserId': self.author_user_id,
            'nicknameSnapshot': self.nickname_snapshot,
            'content': self.content,
            'createdAt': self.created_at.isoformat() if self.created_at else None,
            'updatedAt': self.updated_at.isoformat() if self.updated_at else None
        }
