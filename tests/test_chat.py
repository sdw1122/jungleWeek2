import unittest
from unittest.mock import patch

from app import create_app
from app.extensions import db
from app.models import (
    CareLog,
    ChatMessage,
    ChatSession,
    Plant,
    PlantOwnership,
    PlantSpecies,
    User,
)


class ChatApiTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app(
            {
                "TESTING": True,
                "SECRET_KEY": "chat-test-secret",
                "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
                "SESSION_COOKIE_SECURE": False,
                "REMEMBER_COOKIE_SECURE": False,
                "GOOGLE_CLIENT_ID": "",
                "GOOGLE_CLIENT_SECRET": "",
            }
        )
        self.client = self.app.test_client()
        with self.app.app_context():
            db.create_all()
            self.user_id = self._create_user("owner@example.com", "식물주인").id
            species = PlantSpecies(name="몬스테라", category="foliage", emoji="🌿")
            db.session.add(species)
            db.session.flush()
            plant = Plant(species_id=species.id, name="몬스테라", mood="POSITIVE")
            db.session.add(plant)
            db.session.flush()
            db.session.add(
                PlantOwnership(
                    plant_id=plant.id,
                    owner_user_id=self.user_id,
                    acquisition_type="ADOPTION",
                )
            )
            db.session.commit()
            self.plant_id = plant.id
        self._login(self.client, "owner@example.com")

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

    def _csrf(self, client=None):
        active_client = client or self.client
        return active_client.get("/api/v1/auth/csrf").get_json()["data"]["csrfToken"]

    def _login(self, client, email):
        return client.post(
            "/api/v1/auth/login",
            json={"email": email, "password": "password123", "remember": False},
            headers={"X-CSRF-Token": self._csrf(client)},
        )

    def _chat(self, client=None, plant_id=None, message="예쁘게 자라줘"):
        active_client = client or self.client
        return active_client.post(
            "/api/chat",
            json={"plant_id": plant_id or self.plant_id, "message": message},
            headers={"X-CSRF-Token": self._csrf(active_client)},
        )

    @patch(
        "app.routes.chat.analyze_chat",
        return_value={
            "sentiment": "POSITIVE",
            "response": "고마워요! 🌱",
            "emotion": "기쁨",
            "positive_delta": 4,
            "negative_delta": 0,
        },
    )
    def test_chat_saves_messages_and_updates_owned_plant(self, analyze_chat):
        with self.app.app_context():
            db.session.add(
                CareLog(
                    plant_id=self.plant_id,
                    user_id=self.user_id,
                    action_type="IGNORE",
                    growth_delta=5,
                    negative_delta=5,
                )
            )
            db.session.commit()

        response = self._chat()

        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertEqual(payload["response"], "고마워요! 🌱")
        self.assertEqual(payload["positiveDelta"], 4)
        self.assertEqual(payload["negativeDelta"], 0)
        self.assertEqual(payload["plant"]["growthScore"], 0)
        self.assertEqual(payload["plant"]["positiveEnergy"], 4)
        self.assertEqual(payload["plant"]["mood"], "기쁨")
        analyze_chat.assert_called_once_with("예쁘게 자라줘", [], 0, 0, 0, "IGNORE")

        with self.app.app_context():
            self.assertEqual(ChatSession.query.count(), 1)
            self.assertEqual(ChatMessage.query.count(), 2)
            self.assertEqual(
                [item.role for item in ChatMessage.query.order_by(ChatMessage.id)],
                ["USER", "PLANT"],
            )
            plant = db.session.get(Plant, self.plant_id)
            self.assertEqual(plant.growth_score, 0)
            self.assertEqual(plant.mood, "기쁨")

    def test_other_user_cannot_chat_with_plant(self):
        with self.app.app_context():
            self._create_user("other@example.com", "다른사용자")
        other_client = self.app.test_client()
        self.assertEqual(self._login(other_client, "other@example.com").status_code, 200)

        response = self._chat(client=other_client)

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.get_json()["error"]["code"], "PLANT_NOT_FOUND")

    def test_chat_requires_login_csrf_and_valid_message(self):
        anonymous = self.app.test_client()
        self.assertEqual(
            anonymous.post(
                "/api/chat",
                json={"plant_id": self.plant_id, "message": "안녕"},
            ).status_code,
            403,
        )
        self.assertEqual(self._chat(message="").status_code, 400)


if __name__ == "__main__":
    unittest.main()
