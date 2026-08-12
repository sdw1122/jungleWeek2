import os
import unittest
from datetime import date, datetime, timezone
from unittest.mock import patch

from app import create_app
from app.extensions import db
from app.models import (
    CareLog,
    ChatMessage,
    ChatSession,
    DiaryEntry,
    Gift,
    Plant,
    PlantOwnership,
    PlantSpecies,
    User,
)
from app.services.diary_service import generate_diary_draft


FIXED_DAY = date(2026, 8, 12)


class DiaryApiTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app(
            {
                "TESTING": True,
                "SECRET_KEY": "diary-test-secret",
                "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
                "SESSION_COOKIE_SECURE": False,
                "REMEMBER_COOKIE_SECURE": False,
                "GOOGLE_CLIENT_ID": "",
                "GOOGLE_CLIENT_SECRET": "",
            }
        )
        self.owner_client = self.app.test_client()
        self.recipient_client = self.app.test_client()
        self.other_client = self.app.test_client()
        with self.app.app_context():
            db.create_all()
            owner = self._create_user("owner@example.com", "일기주인")
            recipient = self._create_user("recipient@example.com", "새주인")
            other = self._create_user("other@example.com", "외부인")
            self.owner_id = owner.id
            self.recipient_id = recipient.id
            self.other_id = other.id
            species = PlantSpecies(name="몬스테라", category="foliage", emoji="🌿")
            db.session.add(species)
            db.session.flush()
            plant = Plant(
                species_id=species.id,
                name="사랑을 담은 몬스테라",
                growth_score=45,
                positive_energy=20,
                negative_energy=5,
                mood="기쁨",
                status="GROWING",
            )
            db.session.add(plant)
            db.session.flush()
            db.session.add(
                PlantOwnership(
                    plant_id=plant.id,
                    owner_user_id=owner.id,
                    acquisition_type="ADOPTION",
                )
            )
            db.session.commit()
            self.plant_id = plant.id
        self._login(self.owner_client, "owner@example.com")
        self._login(self.recipient_client, "recipient@example.com")
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

    def _request(self, client, method, path, payload=None, csrf=True):
        headers = {"X-CSRF-Token": self._csrf(client)} if csrf else {}
        return client.open(path, method=method, json=payload, headers=headers)

    def _save_today(self, title="오늘의 성장", content="오늘도 조금 더 자랐다."):
        with patch("app.routes.diary._seoul_today", return_value=FIXED_DAY):
            return self._request(
                self.owner_client,
                "PUT",
                f"/api/v1/plants/{self.plant_id}/diary/today",
                {"title": title, "content": content},
            )

    def _create_diary(self, author_id, diary_date, title):
        entry = DiaryEntry(
            plant_id=self.plant_id,
            author_user_id=author_id,
            title=title,
            content=f"{title} 내용",
            source_type="AI",
            mood_snapshot="기쁨",
            growth_score_snapshot=45,
            positive_energy_snapshot=20,
            negative_energy_snapshot=5,
            growth_stage_snapshot="BUD",
            growth_tendency_snapshot="POSITIVE",
            is_public=False,
            diary_date=diary_date,
            activity_summary={"careActions": [], "chat": {}, "totals": {}},
        )
        db.session.add(entry)
        db.session.commit()
        return entry

    def _transfer_plant(self):
        now = datetime(2026, 8, 12, 12, tzinfo=timezone.utc)
        ownership = PlantOwnership.query.filter_by(
            plant_id=self.plant_id,
            ended_at=None,
        ).one()
        gift = Gift(
            plant_id=self.plant_id,
            sender_user_id=self.owner_id,
            recipient_user_id=self.recipient_id,
            recipient_name="새주인",
            gifted_on=FIXED_DAY,
            status="ACCEPTED",
            accepted_at=now,
        )
        db.session.add(gift)
        db.session.flush()
        ownership.ended_at = now
        db.session.add(
            PlantOwnership(
                plant_id=self.plant_id,
                owner_user_id=self.recipient_id,
                acquisition_type="GIFT",
                gift_id=gift.id,
            )
        )
        db.session.get(Plant, self.plant_id).status = "GIFTED"
        db.session.commit()

    def test_draft_uses_today_care_and_recent_chat_without_saving(self):
        created_at = datetime(2026, 8, 12, 3, tzinfo=timezone.utc)
        with self.app.app_context():
            db.session.add(
                CareLog(
                    plant_id=self.plant_id,
                    user_id=self.owner_id,
                    action_type="WATER",
                    growth_delta=5,
                    positive_delta=5,
                    created_at=created_at,
                )
            )
            session = ChatSession(
                plant_id=self.plant_id,
                user_id=self.owner_id,
                started_at=created_at,
            )
            db.session.add(session)
            db.session.flush()
            db.session.add_all(
                [
                    ChatMessage(
                        session_id=session.id,
                        role="USER",
                        content="오늘도 예뻐",
                        created_at=created_at,
                    ),
                    ChatMessage(
                        session_id=session.id,
                        role="PLANT",
                        content="고마워요!",
                        positive_delta=3,
                        created_at=created_at,
                    ),
                ]
            )
            db.session.commit()

        with (
            patch("app.routes.diary._seoul_today", return_value=FIXED_DAY),
            patch(
                "app.routes.diary.generate_diary_draft",
                return_value={
                    "title": "물을 마신 날",
                    "content": "오늘은 뿌리가 촉촉했다.",
                    "fallback": False,
                },
            ) as generator,
        ):
            response = self._request(
                self.owner_client,
                "POST",
                f"/api/v1/plants/{self.plant_id}/diary/draft",
                {},
            )

        self.assertEqual(response.status_code, 200)
        draft = response.get_json()["data"]["draft"]
        self.assertEqual(draft["title"], "물을 마신 날")
        summary = generator.call_args.kwargs["activity_summary"]
        self.assertEqual(summary["careActions"][0]["actionType"], "WATER")
        self.assertEqual(summary["totals"]["positiveDelta"], 8)
        self.assertEqual(len(generator.call_args.kwargs["recent_messages"]), 2)
        with self.app.app_context():
            self.assertEqual(DiaryEntry.query.count(), 0)

    def test_today_save_is_one_per_plant_and_captures_snapshot(self):
        first = self._save_today()
        second = self._save_today("수정된 제목", "하루를 다시 정리했다.")
        self.assertEqual(first.status_code, 201)
        self.assertEqual(second.status_code, 200)
        with self.app.app_context():
            self.assertEqual(DiaryEntry.query.count(), 1)
            entry = DiaryEntry.query.one()
            self.assertEqual(entry.title, "수정된 제목")
            self.assertEqual(entry.author_user_id, self.owner_id)
            self.assertEqual(entry.diary_date, FIXED_DAY)
            self.assertEqual(entry.growth_score_snapshot, 45)
            self.assertEqual(entry.growth_tendency_snapshot, "POSITIVE")
            self.assertFalse(entry.is_public)

    def test_activity_snapshot_does_not_change_after_later_care(self):
        entry_id = self._save_today().get_json()["data"]["entry"]["id"]
        with self.app.app_context():
            db.session.add(
                CareLog(
                    plant_id=self.plant_id,
                    user_id=self.owner_id,
                    action_type="PET",
                    growth_delta=5,
                    positive_delta=5,
                    created_at=datetime(2026, 8, 12, 4, tzinfo=timezone.utc),
                )
            )
            db.session.commit()
        detail = self.owner_client.get(f"/api/v1/diary/{entry_id}")
        self.assertEqual(detail.status_code, 200)
        self.assertEqual(
            detail.get_json()["data"]["entry"]["activitySummary"]["careActions"],
            [],
        )

    def test_empty_day_has_local_ai_fallback(self):
        with patch.dict(os.environ, {"OPENAI_API_KEY": ""}):
            draft = generate_diary_draft(
                plant_name="몬스테라",
                mood="평온",
                growth_score=10,
                positive_energy=0,
                negative_energy=0,
                latest_care_action=None,
                activity_summary={
                    "careActions": [],
                    "chat": {"messageCount": 0},
                    "totals": {},
                },
                recent_messages=[],
            )
        self.assertTrue(draft["fallback"])
        self.assertIn("조용히", draft["title"])
        self.assertIn("돌봄이나 대화 없이", draft["content"])

    def test_owner_and_original_author_permissions_after_gift(self):
        with self.app.app_context():
            original = self._create_diary(self.owner_id, date(2026, 8, 10), "원래 주인의 기록")
            original_id = original.id
            self._transfer_plant()
            future = self._create_diary(self.recipient_id, date(2026, 8, 13), "새 주인의 기록")
            future_id = future.id

        owner_month = self.owner_client.get(
            f"/api/v1/plants/{self.plant_id}/diary?year=2026&month=8"
        )
        recipient_month = self.recipient_client.get(
            f"/api/v1/plants/{self.plant_id}/diary?year=2026&month=8"
        )
        self.assertEqual(
            [item["id"] for item in owner_month.get_json()["data"]["entries"]],
            [original_id],
        )
        self.assertEqual(
            [item["id"] for item in recipient_month.get_json()["data"]["entries"]],
            [original_id, future_id],
        )
        self.assertEqual(
            self.owner_client.get(f"/api/v1/diary/{future_id}").status_code,
            404,
        )

        recipient_edit = self._request(
            self.recipient_client,
            "PATCH",
            f"/api/v1/diary/{original_id}",
            {"title": "새 주인이 다듬음", "content": "이어받은 기록을 정리했다."},
        )
        author_edit = self._request(
            self.owner_client,
            "PATCH",
            f"/api/v1/diary/{original_id}",
            {"title": "작성자가 다시 다듬음", "content": "나의 기록을 다시 정리했다."},
        )
        self.assertEqual(recipient_edit.status_code, 200)
        self.assertEqual(author_edit.status_code, 200)
        self.assertEqual(
            self.other_client.get(f"/api/v1/diary/{original_id}").status_code,
            404,
        )

    def test_month_boundaries_and_accessible_plant_types(self):
        with self.app.app_context():
            august = self._create_diary(self.owner_id, date(2026, 8, 31), "8월 기록")
            august_id = august.id
        august_response = self.owner_client.get(
            f"/api/v1/plants/{self.plant_id}/diary?year=2026&month=8"
        )
        september_response = self.owner_client.get(
            f"/api/v1/plants/{self.plant_id}/diary?year=2026&month=9"
        )
        self.assertEqual(
            [item["id"] for item in august_response.get_json()["data"]["entries"]],
            [august_id],
        )
        self.assertEqual(september_response.get_json()["data"]["entries"], [])
        plants = self.owner_client.get("/api/v1/diary/plants").get_json()["data"]["plants"]
        self.assertEqual(plants[0]["accessType"], "OWNER")

        with self.app.app_context():
            self._transfer_plant()
        archived = self.owner_client.get("/api/v1/diary/plants").get_json()["data"]["plants"]
        self.assertEqual(archived[0]["accessType"], "AUTHOR_ARCHIVE")

    def test_non_owner_cannot_create_and_validation_requires_csrf(self):
        draft = self._request(
            self.other_client,
            "POST",
            f"/api/v1/plants/{self.plant_id}/diary/draft",
            {},
        )
        save = self._request(
            self.other_client,
            "PUT",
            f"/api/v1/plants/{self.plant_id}/diary/today",
            {"title": "제목", "content": "내용"},
        )
        no_csrf = self._request(
            self.owner_client,
            "PUT",
            f"/api/v1/plants/{self.plant_id}/diary/today",
            {"title": "제목", "content": "내용"},
            csrf=False,
        )
        invalid = self._request(
            self.owner_client,
            "PUT",
            f"/api/v1/plants/{self.plant_id}/diary/today",
            {"title": "", "content": "x" * 2001},
        )
        self.assertEqual(draft.status_code, 403)
        self.assertEqual(save.status_code, 403)
        self.assertEqual(no_csrf.status_code, 403)
        self.assertEqual(invalid.status_code, 400)


if __name__ == "__main__":
    unittest.main()
