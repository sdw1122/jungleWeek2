import unittest

from app import create_app
from app.extensions import db


class DeploymentConfigTestCase(unittest.TestCase):
    def test_production_rejects_weak_secret(self):
        with self.assertRaisesRegex(RuntimeError, "SECRET_KEY"):
            create_app(
                {
                    "APP_ENV": "production",
                    "SECRET_KEY": "short",
                    "SESSION_COOKIE_SECURE": True,
                    "TRUST_PROXY": True,
                    "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
                }
            )

    def test_production_requires_secure_cookies(self):
        with self.assertRaisesRegex(RuntimeError, "SESSION_COOKIE_SECURE"):
            create_app(
                {
                    "APP_ENV": "production",
                    "SECRET_KEY": "a" * 32,
                    "SESSION_COOKIE_SECURE": False,
                    "TRUST_PROXY": True,
                    "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
                }
            )

    def test_proxy_https_adds_security_headers(self):
        app = create_app(
            {
                "TESTING": True,
                "SECRET_KEY": "test-secret-key",
                "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
                "TRUST_PROXY": True,
            }
        )
        response = app.test_client().get(
            "/health",
            headers={
                "X-Forwarded-For": "203.0.113.10",
                "X-Forwarded-Proto": "https",
                "X-Forwarded-Host": "farmda.example",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn("max-age=31536000", response.headers["Strict-Transport-Security"])
        self.assertEqual(response.headers["X-Content-Type-Options"], "nosniff")
        self.assertEqual(response.headers["X-Frame-Options"], "SAMEORIGIN")
        with app.app_context():
            db.session.remove()
            db.engine.dispose()


if __name__ == "__main__":
    unittest.main()
