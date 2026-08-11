import unittest
from unittest.mock import patch

from app import create_app
from app.extensions import db, oauth
from app.models import User
from app.routes.auth import GoogleAccountError, find_or_create_google_user


class AuthApiTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app(
            {
                "TESTING": True,
                "SECRET_KEY": "test-secret-key",
                "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
                "SESSION_COOKIE_SECURE": False,
                "REMEMBER_COOKIE_SECURE": False,
                "GOOGLE_CLIENT_ID": "test-google-client-id",
                "GOOGLE_CLIENT_SECRET": "test-google-client-secret",
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

    def test_legacy_dashboard_redirects_to_current_dashboard(self):
        self.signup()
        self.post(
            "/api/v1/auth/login",
            {
                "email": "user@example.com",
                "password": "password123",
                "remember": False,
            },
        )
        response = self.client.get("/dashboard.html?plantId=12")
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.location.endswith("/dashboard-v2.html?plantId=12"))

    def test_google_login_requires_configuration(self):
        self.app.config["GOOGLE_CLIENT_ID"] = ""
        response = self.client.get("/api/v1/auth/google")
        self.assertEqual(response.status_code, 302)
        self.assertIn("/login.html?oauthError=not_configured", response.location)

    def test_google_callback_creates_user_and_logs_in(self):
        profile = {
            "sub": "google-subject-123",
            "email": "GOOGLE@Example.com",
            "email_verified": True,
            "name": "초록이",
            "picture": "https://example.com/profile.png",
        }
        with patch.object(
            oauth.google,
            "authorize_access_token",
            return_value={"userinfo": profile},
        ):
            response = self.client.get("/api/v1/auth/google/callback")

        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.location.endswith("/welcome.html"))
        self.assertEqual(self.client.get("/api/v1/auth/me").status_code, 200)
        with self.app.app_context():
            user = User.query.one()
            self.assertEqual(user.email, "google@example.com")
            self.assertEqual(user.auth_provider, "GOOGLE")
            self.assertEqual(user.google_subject, "google-subject-123")
            self.assertIsNone(user.password_hash)

    def test_google_profile_reuses_subject_and_keeps_unique_nickname(self):
        with self.app.app_context():
            first = find_or_create_google_user(
                {
                    "sub": "google-1",
                    "email": "first@example.com",
                    "email_verified": True,
                    "name": "초록이",
                }
            )
            second = find_or_create_google_user(
                {
                    "sub": "google-2",
                    "email": "second@example.com",
                    "email_verified": True,
                    "name": "초록이",
                }
            )
            reused = find_or_create_google_user(
                {
                    "sub": "google-1",
                    "email": "first@example.com",
                    "email_verified": True,
                    "name": "변경된 이름",
                }
            )
            self.assertEqual(first.id, reused.id)
            self.assertEqual(second.nickname, "초록이-2")
            self.assertEqual(User.query.count(), 2)

    def test_google_profile_does_not_auto_link_local_account(self):
        self.assertEqual(self.signup().status_code, 201)
        with self.app.app_context():
            with self.assertRaises(GoogleAccountError) as context:
                find_or_create_google_user(
                    {
                        "sub": "google-subject-duplicate",
                        "email": "user@example.com",
                        "email_verified": True,
                        "name": "초록이",
                    }
                )
            self.assertEqual(context.exception.code, "account_exists")

    def test_google_profile_requires_verified_email(self):
        with self.app.app_context():
            with self.assertRaises(GoogleAccountError) as context:
                find_or_create_google_user(
                    {
                        "sub": "google-unverified",
                        "email": "unverified@example.com",
                        "email_verified": False,
                        "name": "미인증 사용자",
                    }
                )
            self.assertEqual(context.exception.code, "email_unverified")


if __name__ == "__main__":
    unittest.main()
