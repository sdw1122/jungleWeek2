import unittest

from app import create_app
from app.extensions import db
from app.models import (
    GuestbookEntry,
    GuestbookReaction,
    GuestbookReply,
    GuestbookReplyReaction,
    User,
)


class GuestbookApiTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app(
            {
                "TESTING": True,
                "SECRET_KEY": "guestbook-test-secret",
                "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
                "SESSION_COOKIE_SECURE": False,
                "REMEMBER_COOKIE_SECURE": False,
                "GOOGLE_CLIENT_ID": "",
                "GOOGLE_CLIENT_SECRET": "",
            }
        )
        self.owner_client = self.app.test_client()
        self.other_client = self.app.test_client()
        with self.app.app_context():
            db.create_all()
            self.owner_id = self._create_user("owner@example.com", "초록정원사").id
            self.other_id = self._create_user("other@example.com", "다육이엄마").id
        self._login(self.owner_client, "owner@example.com")
        self._login(self.other_client, "other@example.com")

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.drop_all()
            db.engine.dispose()

    def _create_user(self, email, nickname):
        user = User(
            email=email,
            nickname=nickname,
            auth_provider="LOCAL",
            status="ACTIVE",
        )
        user.set_password("password123")
        db.session.add(user)
        db.session.commit()
        return user

    def _csrf(self, client):
        return client.get("/api/v1/auth/csrf").get_json()["data"]["csrfToken"]

    def _login(self, client, email):
        return client.post(
            "/api/v1/auth/login",
            json={"email": email, "password": "password123", "remember": False},
            headers={"X-CSRF-Token": self._csrf(client)},
        )

    def _request(self, client, method, path, payload=None):
        return client.open(
            path,
            method=method,
            json=payload,
            headers={"X-CSRF-Token": self._csrf(client)},
        )

    def _create_entry(self, content="반가워요 🌱"):
        return self._request(
            self.owner_client,
            "POST",
            "/api/v1/guestbook",
            {"content": content},
        )

    def test_entry_crud_uses_authenticated_database_user(self):
        created = self._create_entry()
        self.assertEqual(created.status_code, 201)
        entry = created.get_json()["data"]
        self.assertEqual(entry["author"], "초록정원사")
        self.assertEqual(entry["authorUserId"], self.owner_id)

        listed = self.owner_client.get("/api/v1/guestbook").get_json()["data"]
        self.assertEqual(len(listed), 1)
        self.assertEqual(listed[0]["content"], "반가워요 🌱")

        forbidden = self._request(
            self.other_client,
            "PUT",
            f'/api/v1/guestbook/{entry["id"]}',
            {"content": "가로채기"},
        )
        self.assertEqual(forbidden.status_code, 403)

        updated = self._request(
            self.owner_client,
            "PUT",
            f'/api/v1/guestbook/{entry["id"]}',
            {"content": "수정했어요"},
        )
        self.assertEqual(updated.status_code, 200)
        self.assertEqual(updated.get_json()["data"]["content"], "수정했어요")

        deleted = self._request(
            self.owner_client,
            "DELETE",
            f'/api/v1/guestbook/{entry["id"]}',
        )
        self.assertEqual(deleted.status_code, 200)
        with self.app.app_context():
            self.assertEqual(GuestbookEntry.query.count(), 0)

    def test_entry_reaction_toggles_and_switches_once_per_user(self):
        entry_id = self._create_entry().get_json()["data"]["id"]
        path = f"/api/v1/guestbook/{entry_id}/reaction"

        liked = self._request(self.other_client, "POST", path, {"type": "like"})
        self.assertEqual(liked.status_code, 200)
        self.assertEqual(liked.get_json()["data"]["reactions"]["likedBy"], ["다육이엄마"])

        disliked = self._request(
            self.other_client, "POST", path, {"type": "dislike"}
        )
        reactions = disliked.get_json()["data"]["reactions"]
        self.assertEqual(reactions["likedBy"], [])
        self.assertEqual(reactions["dislikedBy"], ["다육이엄마"])

        removed = self._request(
            self.other_client, "POST", path, {"type": "dislike"}
        )
        self.assertEqual(removed.get_json()["data"]["reactions"]["dislikedBy"], [])
        with self.app.app_context():
            self.assertEqual(GuestbookReaction.query.count(), 0)

    def test_reply_and_reply_reaction_are_persisted(self):
        entry_id = self._create_entry().get_json()["data"]["id"]
        reply = self._request(
            self.other_client,
            "POST",
            f"/api/v1/guestbook/{entry_id}/reply",
            {"content": "저도 반가워요"},
        )
        self.assertEqual(reply.status_code, 201)
        reply_data = reply.get_json()["data"]["replies"][0]
        self.assertEqual(reply_data["author"], "다육이엄마")

        reaction = self._request(
            self.owner_client,
            "POST",
            f'/api/v1/guestbook/reply/{reply_data["id"]}/reaction',
            {"type": "like"},
        )
        self.assertEqual(reaction.status_code, 200)
        self.assertEqual(
            reaction.get_json()["data"]["reactions"]["likedBy"],
            ["초록정원사"],
        )
        with self.app.app_context():
            self.assertEqual(GuestbookReply.query.count(), 1)
            self.assertEqual(GuestbookReplyReaction.query.count(), 1)

    def test_mutations_require_login_and_csrf(self):
        anonymous = self.app.test_client()
        self.assertEqual(anonymous.get("/api/v1/guestbook").status_code, 200)
        self.assertEqual(
            anonymous.post(
                "/api/v1/guestbook",
                json={"content": "로그인 없이 작성"},
            ).status_code,
            403,
        )
        self.assertEqual(
            self.owner_client.post(
                "/api/v1/guestbook",
                json={"content": "CSRF 없음"},
            ).status_code,
            403,
        )


if __name__ == "__main__":
    unittest.main()
