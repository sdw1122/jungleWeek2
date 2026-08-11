import unittest

from app import create_app
from app.extensions import db
from app.models import User


class AuthApiTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app(
            {
                "TESTING": True,
                "SECRET_KEY": "test-secret-key",
                "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
                "SESSION_COOKIE_SECURE": False,
                "REMEMBER_COOKIE_SECURE": False,
            }
        )
        self.client = self.app.test_client()
        with self.app.app_context():
            db.create_all()

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.drop_all()
            db.engine.dispose()

    def csrf_token(self):
        response = self.client.get("/api/v1/auth/csrf")
        self.assertEqual(response.status_code, 200)
        return response.get_json()["data"]["csrfToken"]

    def post(self, path, payload, token=None):
        headers = {"X-CSRF-Token": token or self.csrf_token()}
        return self.client.post(path, json=payload, headers=headers)

    def signup(self):
        return self.post(
            "/api/v1/auth/signup",
            {
                "nickname": "초록이",
                "email": "USER@Example.com",
                "password": "password123",
            },
        )

    def test_signup_creates_local_user_with_hashed_password(self):
        response = self.signup()
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.get_json()["data"]["user"]["email"], "user@example.com")

        with self.app.app_context():
            user = User.query.one()
            self.assertNotEqual(user.password_hash, "password123")
            self.assertTrue(user.check_password("password123"))

    def test_signup_rejects_duplicate_email(self):
        self.assertEqual(self.signup().status_code, 201)
        response = self.post(
            "/api/v1/auth/signup",
            {
                "nickname": "다른별명",
                "email": "user@example.com",
                "password": "password456",
            },
        )
        self.assertEqual(response.status_code, 409)
        self.assertEqual(response.get_json()["error"]["code"], "EMAIL_ALREADY_EXISTS")

    def test_login_me_and_logout(self):
        self.signup()
        login_response = self.post(
            "/api/v1/auth/login",
            {
                "email": "user@example.com",
                "password": "password123",
                "remember": True,
            },
        )
        self.assertEqual(login_response.status_code, 200)

        me_response = self.client.get("/api/v1/auth/me")
        self.assertEqual(me_response.status_code, 200)
        self.assertEqual(me_response.get_json()["data"]["user"]["nickname"], "초록이")
        self.assertEqual(self.client.get("/welcome.html").status_code, 200)

        csrf_token = login_response.get_json()["data"]["csrfToken"]
        logout_response = self.client.post(
            "/api/v1/auth/logout",
            headers={"X-CSRF-Token": csrf_token},
        )
        self.assertEqual(logout_response.status_code, 200)
        self.assertEqual(self.client.get("/api/v1/auth/me").status_code, 401)

    def test_login_rejects_wrong_password(self):
        self.signup()
        response = self.post(
            "/api/v1/auth/login",
            {
                "email": "user@example.com",
                "password": "wrong-password",
                "remember": False,
            },
        )
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.get_json()["error"]["code"], "INVALID_CREDENTIALS")

    def test_mutating_request_requires_csrf_token(self):
        response = self.client.post(
            "/api/v1/auth/signup",
            json={
                "nickname": "초록이",
                "email": "user@example.com",
                "password": "password123",
            },
        )
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.get_json()["error"]["code"], "CSRF_TOKEN_INVALID")

    def test_protected_page_redirects_to_login(self):
        response = self.client.get("/dashboard-v2.html")
        self.assertEqual(response.status_code, 302)
        self.assertIn("/login.html?next=/dashboard-v2.html", response.location)


if __name__ == "__main__":
    unittest.main()
