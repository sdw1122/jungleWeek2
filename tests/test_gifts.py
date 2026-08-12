import unittest
from unittest.mock import patch

from app import create_app
from app.extensions import db
from app.models import (
    ChatMessage,
    ChatSession,
    Gift,
    Plant,
    PlantOwnership,
    PlantSpecies,
    User,
)
from app.services.epithet_service import assign_plant_epithet


class GiftApiTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app(
            {
                "TESTING": True,
                "SECRET_KEY": "gift-test-secret",
                "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
                "SESSION_COOKIE_SECURE": False,
                "REMEMBER_COOKIE_SECURE": False,
                "GOOGLE_CLIENT_ID": "",
                "GOOGLE_CLIENT_SECRET": "",
            }
        )
        self.owner_client = self.app.test_client()
        self.recipient_client = self.app.test_client()
        self.third_client = self.app.test_client()
        with self.app.app_context():
            db.create_all()
            owner = self._create_user("owner@example.com", "식물주인")
            recipient = self._create_user("recipient@example.com", "선물친구")
            third = self._create_user("third@example.com", "다음친구")
            self.owner_id = owner.id
            self.recipient_id = recipient.id
            self.third_id = third.id

            species = PlantSpecies(name="몬스테라", category="foliage", emoji="🌿")
            db.session.add(species)
            db.session.flush()
            plant = Plant(
                species_id=species.id,
                name="몬스테라",
                growth_score=100,
                positive_energy=25,
                negative_energy=5,
                mood="기쁨",
                status="GIFT_READY",
            )
            assign_plant_epithet(plant)
            db.session.add(plant)
            db.session.flush()
            db.session.add(
                PlantOwnership(
                    plant_id=plant.id,
                    owner_user_id=owner.id,
                    acquisition_type="ADOPTION",
                )
            )
            session = ChatSession(plant_id=plant.id, user_id=owner.id)
            db.session.add(session)
            db.session.flush()
            db.session.add_all(
                [
                    ChatMessage(session_id=session.id, role="USER", content="잘 자랐구나"),
                    ChatMessage(session_id=session.id, role="PLANT", content="고마워요!"),
                ]
            )
            db.session.commit()
            self.plant_id = plant.id

        self._login(self.owner_client, "owner@example.com")
        self._login(self.recipient_client, "recipient@example.com")
        self._login(self.third_client, "third@example.com")

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

    def _post(self, client, path, payload):
        return client.post(
            path,
            json=payload,
            headers={"X-CSRF-Token": self._csrf(client)},
        )

    def _gift(self, client=None, nickname="선물친구", message="소중히 키웠어"):
        return self._post(
            client or self.owner_client,
            f"/api/v1/plants/{self.plant_id}/gift",
            {"recipientNickname": nickname, "message": message},
        )

    def test_gift_moves_ownership_and_preserves_history(self):
        with self.app.app_context():
            original = db.session.get(Plant, self.plant_id)
            original_pair = (
                original.epithet_first_id,
                original.epithet_second_id,
            )
            original_display_name = original.display_name

        response = self._gift()
        self.assertEqual(response.status_code, 201)
        response_data = response.get_json()["data"]
        gift_id = response_data["gift"]["id"]
        self.assertEqual(response_data["plant"]["id"], self.plant_id)
        self.assertEqual(response_data["plant"]["status"], "GIFTED")

        with self.app.app_context():
            gift = db.session.get(Gift, gift_id)
            self.assertEqual(gift.status, "ACCEPTED")
            self.assertIsNotNone(gift.accepted_at)
            self.assertEqual(gift.recipient_user_id, self.recipient_id)
            ownerships = PlantOwnership.query.order_by(PlantOwnership.id).all()
            self.assertIsNotNone(ownerships[0].ended_at)
            self.assertEqual(ownerships[1].owner_user_id, self.recipient_id)
            self.assertEqual(ownerships[1].acquisition_type, "GIFT")
            self.assertEqual(ownerships[1].gift_id, gift_id)
            gifted_plant = db.session.get(Plant, self.plant_id)
            self.assertEqual(gifted_plant.status, "GIFTED")
            self.assertEqual(
                (gifted_plant.epithet_first_id, gifted_plant.epithet_second_id),
                original_pair,
            )
            self.assertIsNotNone(ChatSession.query.one().ended_at)

        self.assertEqual(
            self.owner_client.get("/api/v1/plants").get_json()["data"]["plants"],
            [],
        )
        received = self.recipient_client.get(f"/api/v1/plants/{self.plant_id}")
        self.assertEqual(received.status_code, 200)
        plant = received.get_json()["data"]["plant"]
        self.assertEqual(plant["growthScore"], 100)
        self.assertEqual(plant["positiveEnergy"], 25)
        self.assertEqual(plant["mood"], "기쁨")
        self.assertEqual(plant["displayName"], original_display_name)
        self.assertEqual(plant["receivedGift"]["message"], "소중히 키웠어")

        history = self.recipient_client.get(f"/api/chat/{self.plant_id}/messages")
        self.assertEqual(history.status_code, 200)
        self.assertEqual(
            [item["content"] for item in history.get_json()["data"]["messages"]],
            ["잘 자랐구나", "고마워요!"],
        )
        self.assertEqual(
            history.get_json()["data"]["messages"][0]["speakerNickname"],
            "식물주인",
        )
        self.assertEqual(
            self.owner_client.get(f"/api/chat/{self.plant_id}/messages").status_code,
            404,
        )

    def test_received_gift_is_acknowledged_once(self):
        gift_id = self._gift().get_json()["data"]["gift"]["id"]
        path = f"/api/v1/gifts/{gift_id}/acknowledge"
        first = self._post(self.recipient_client, path, {})
        second = self._post(self.recipient_client, path, {})
        self.assertEqual(first.status_code, 200)
        self.assertEqual(second.status_code, 200)
        self.assertIsNotNone(first.get_json()["data"]["gift"]["recipientViewedAt"])
        detail = self.recipient_client.get(f"/api/v1/plants/{self.plant_id}")
        self.assertIsNone(detail.get_json()["data"]["plant"]["receivedGift"])

    @patch(
        "app.routes.chat.analyze_chat",
        return_value={
            "sentiment": "POSITIVE",
            "response": "새 주인님도 반가워요!",
            "emotion": "반가움",
            "positive_delta": 2,
            "negative_delta": 0,
        },
    )
    def test_new_owner_ai_continues_previous_conversation(self, analyze_chat):
        self.assertEqual(self._gift().status_code, 201)
        response = self._post(
            self.recipient_client,
            "/api/chat",
            {"plant_id": self.plant_id, "message": "우리도 잘 지내보자"},
        )
        self.assertEqual(response.status_code, 200)
        history = analyze_chat.call_args.args[1]
        self.assertEqual(
            history,
            [
                {"role": "USER", "content": "잘 자랐구나"},
                {"role": "PLANT", "content": "고마워요!"},
            ],
        )

    def test_rejects_invalid_gift_requests(self):
        missing = self._gift(nickname="없는친구")
        self.assertEqual(missing.status_code, 404)
        self.assertEqual(missing.get_json()["error"]["code"], "RECIPIENT_NOT_FOUND")

        self_gift = self._gift(nickname="식물주인")
        self.assertEqual(self_gift.status_code, 409)
        self.assertEqual(self_gift.get_json()["error"]["code"], "SELF_GIFT_NOT_ALLOWED")

        with self.app.app_context():
            plant = db.session.get(Plant, self.plant_id)
            plant.growth_score = 95
            plant.status = "GROWING"
            db.session.commit()
        immature = self._gift()
        self.assertEqual(immature.status_code, 409)
        self.assertEqual(immature.get_json()["error"]["code"], "PLANT_NOT_GIFT_READY")

        no_csrf = self.owner_client.post(
            f"/api/v1/plants/{self.plant_id}/gift",
            json={"recipientNickname": "선물친구"},
        )
        self.assertEqual(no_csrf.status_code, 403)
        anonymous = self.app.test_client()
        unauthenticated = anonymous.post(
            f"/api/v1/plants/{self.plant_id}/gift",
            json={"recipientNickname": "선물친구"},
            headers={"X-CSRF-Token": self._csrf(anonymous)},
        )
        self.assertEqual(unauthenticated.status_code, 401)

    def test_completed_received_plant_can_be_cared_for_and_regifted(self):
        self.assertEqual(self._gift().status_code, 201)
        care = self._post(
            self.recipient_client,
            f"/api/v1/plants/{self.plant_id}/care",
            {"actionType": "WATER"},
        )
        self.assertEqual(care.status_code, 200)
        cared_plant = care.get_json()["data"]["plant"]
        self.assertEqual(cared_plant["growthScore"], 100)
        self.assertEqual(cared_plant["positiveEnergy"], 30)
        self.assertEqual(cared_plant["status"], "GIFTED")

        regift = self._gift(
            client=self.recipient_client,
            nickname="다음친구",
            message="이제 네가 돌봐줘",
        )
        self.assertEqual(regift.status_code, 201)
        third_list = self.third_client.get("/api/v1/plants").get_json()["data"]["plants"]
        self.assertEqual([plant["id"] for plant in third_list], [self.plant_id])

        duplicate = self._gift(client=self.recipient_client, nickname="식물주인")
        self.assertEqual(duplicate.status_code, 409)
        self.assertEqual(
            duplicate.get_json()["error"]["code"],
            "PLANT_OWNERSHIP_CHANGED",
        )


if __name__ == "__main__":
    unittest.main()
