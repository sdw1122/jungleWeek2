import unittest

from app import create_app
from app.extensions import db
from app.models import (
    CareLog,
    Plant,
    PlantEpithetFragment,
    PlantOwnership,
    PlantSpecies,
    User,
)


class PlantApiTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app(
            {
                "TESTING": True,
                "SECRET_KEY": "plant-test-secret",
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
            self.user = self._create_user("owner@example.com", "식물주인")
            self.user_id = self.user.id
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
        response = active_client.get("/api/v1/auth/csrf")
        return response.get_json()["data"]["csrfToken"]

    def _login(self, client, email):
        return client.post(
            "/api/v1/auth/login",
            json={
                "email": email,
                "password": "password123",
                "remember": False,
            },
            headers={"X-CSRF-Token": self._csrf(client)},
        )

    def _post(self, path, payload, client=None):
        active_client = client or self.client
        return active_client.post(
            path,
            json=payload,
            headers={"X-CSRF-Token": self._csrf(active_client)},
        )

    def _create_plant(self, name="몬스테라", client=None):
        return self._post(
            "/api/v1/plants",
            {
                "name": name,
                "speciesName": name,
                "category": "foliage",
                "emoji": "🌿",
                "imageUrl": "https://example.com/monstera.jpg",
            },
            client,
        )

    def test_create_plant_saves_ownership_and_lists_it(self):
        response = self._create_plant()
        self.assertEqual(response.status_code, 201)
        plant_data = response.get_json()["data"]["plant"]
        self.assertEqual(plant_data["growthScore"], 0)
        self.assertEqual(plant_data["stageLabel"], "씨앗")
        self.assertEqual(plant_data["emoji"], "🌿")
        self.assertIsNone(plant_data["mood"])
        self.assertEqual(plant_data["name"], "몬스테라")
        self.assertEqual(plant_data["epithet"]["polarity"], "POSITIVE")
        self.assertTrue(plant_data["displayName"].endswith(" 몬스테라"))
        self.assertEqual(
            plant_data["displayName"],
            f'{plant_data["epithet"]["first"]} '
            f'{plant_data["epithet"]["second"]} 몬스테라',
        )

        list_response = self.client.get("/api/v1/plants")
        self.assertEqual(list_response.status_code, 200)
        self.assertEqual(len(list_response.get_json()["data"]["plants"]), 1)

        with self.app.app_context():
            self.assertEqual(Plant.query.count(), 1)
            self.assertEqual(PlantSpecies.query.count(), 1)
            self.assertEqual(PlantEpithetFragment.query.count(), 48)
            ownership = PlantOwnership.query.one()
            self.assertEqual(ownership.owner_user_id, self.user_id)
            self.assertIsNone(ownership.ended_at)

    def test_same_species_reuses_species_but_allows_multiple_plants(self):
        self.assertEqual(self._create_plant().status_code, 201)
        self.assertEqual(self._create_plant().status_code, 201)
        with self.app.app_context():
            self.assertEqual(Plant.query.count(), 2)
            self.assertEqual(PlantSpecies.query.count(), 1)

    def test_care_updates_energy_and_writes_logs(self):
        plant_id = self._create_plant().get_json()["data"]["plant"]["id"]
        with self.app.app_context():
            plant = db.session.get(Plant, plant_id)
            plant.mood = "설렘"
            db.session.commit()

        water = self._post(
            f"/api/v1/plants/{plant_id}/care",
            {"actionType": "WATER", "sentiment": "NEGATIVE"},
        )
        ignored = self._post(
            f"/api/v1/plants/{plant_id}/care", {"actionType": "IGNORE"}
        )

        self.assertEqual(water.status_code, 200)
        self.assertEqual(ignored.status_code, 200)
        plant_data = ignored.get_json()["data"]["plant"]
        self.assertEqual(plant_data["growthScore"], 10)
        self.assertEqual(plant_data["positiveEnergy"], 5)
        self.assertEqual(plant_data["negativeEnergy"], 5)
        self.assertEqual(plant_data["stageLabel"], "떡잎")
        self.assertEqual(plant_data["mood"], "설렘")

        with self.app.app_context():
            logs = CareLog.query.order_by(CareLog.id).all()
            self.assertEqual([log.action_type for log in logs], ["WATER", "IGNORE"])
            self.assertEqual([log.growth_delta for log in logs], [5, 5])
            self.assertEqual(logs[0].positive_delta, 5)
            self.assertEqual(logs[1].negative_delta, 5)

    def test_other_user_cannot_see_or_update_plant(self):
        plant_id = self._create_plant().get_json()["data"]["plant"]["id"]
        with self.app.app_context():
            self._create_user("other@example.com", "다른사용자")
        other_client = self.app.test_client()
        self.assertEqual(self._login(other_client, "other@example.com").status_code, 200)

        other_list = other_client.get("/api/v1/plants")
        other_detail = other_client.get(f"/api/v1/plants/{plant_id}")
        other_care = self._post(
            f"/api/v1/plants/{plant_id}/care",
            {"actionType": "WATER"},
            other_client,
        )
        self.assertEqual(other_list.get_json()["data"]["plants"], [])
        self.assertEqual(other_detail.status_code, 404)
        self.assertEqual(other_care.status_code, 404)

    def test_completed_plant_keeps_care_actions_enabled(self):
        plant_id = self._create_plant().get_json()["data"]["plant"]["id"]
        with self.app.app_context():
            plant = db.session.get(Plant, plant_id)
            plant.growth_score = 100
            plant.status = "GIFT_READY"
            db.session.commit()

        response = self._post(
            f"/api/v1/plants/{plant_id}/care",
            {"actionType": "WATER"},
        )
        self.assertEqual(response.status_code, 200)
        plant_data = response.get_json()["data"]["plant"]
        self.assertEqual(plant_data["growthScore"], 100)
        self.assertEqual(plant_data["positiveEnergy"], 5)
        self.assertEqual(plant_data["status"], "GIFT_READY")
        with self.app.app_context():
            log = CareLog.query.order_by(CareLog.id.desc()).first()
            self.assertEqual(log.growth_delta, 0)
            self.assertEqual(log.positive_delta, 5)

    def test_stage_change_refreshes_epithet_once(self):
        plant_id = self._create_plant().get_json()["data"]["plant"]["id"]
        with self.app.app_context():
            plant = db.session.get(Plant, plant_id)
            previous_pair = (plant.epithet_first_id, plant.epithet_second_id)

        response = self._post(
            f"/api/v1/plants/{plant_id}/care",
            {"actionType": "WATER"},
        )
        self.assertEqual(response.status_code, 200)
        data = response.get_json()["data"]["plant"]
        self.assertEqual(data["growthStage"], "COTYLEDON")
        self.assertEqual(data["epithet"]["polarity"], "POSITIVE")
        with self.app.app_context():
            plant = db.session.get(Plant, plant_id)
            self.assertNotEqual(
                (plant.epithet_first_id, plant.epithet_second_id),
                previous_pair,
            )

    def test_polarity_flip_refreshes_epithet_within_same_stage(self):
        plant_id = self._create_plant().get_json()["data"]["plant"]["id"]
        with self.app.app_context():
            plant = db.session.get(Plant, plant_id)
            plant.growth_score = 5
            db.session.commit()

        response = self._post(
            f"/api/v1/plants/{plant_id}/care",
            {"actionType": "IGNORE"},
        )
        self.assertEqual(response.status_code, 200)
        data = response.get_json()["data"]["plant"]
        self.assertEqual(data["growthStage"], "COTYLEDON")
        self.assertEqual(data["epithet"]["polarity"], "NEGATIVE")

    def test_same_stage_and_polarity_keep_epithet(self):
        plant_id = self._create_plant().get_json()["data"]["plant"]["id"]
        with self.app.app_context():
            plant = db.session.get(Plant, plant_id)
            plant.growth_score = 5
            previous_pair = (plant.epithet_first_id, plant.epithet_second_id)
            db.session.commit()

        response = self._post(
            f"/api/v1/plants/{plant_id}/care",
            {"actionType": "WATER"},
        )
        self.assertEqual(response.status_code, 200)
        with self.app.app_context():
            plant = db.session.get(Plant, plant_id)
            self.assertEqual(
                (plant.epithet_first_id, plant.epithet_second_id),
                previous_pair,
            )

    def test_plant_api_requires_login_and_csrf(self):
        anonymous = self.app.test_client()
        self.assertEqual(anonymous.get("/api/v1/plants").status_code, 401)
        response = self.client.post(
            "/api/v1/plants",
            json={
                "name": "몬스테라",
                "imageUrl": "https://example.com/plant.jpg",
            },
        )
        self.assertEqual(response.status_code, 403)


if __name__ == "__main__":
    unittest.main()
