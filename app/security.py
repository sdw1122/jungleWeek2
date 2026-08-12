import hmac
import secrets

from flask import Flask, jsonify, request, session


CSRF_SESSION_KEY = "csrf_token"


def get_csrf_token() -> str:
    token = session.get(CSRF_SESSION_KEY)
    if not token:
        token = secrets.token_urlsafe(32)
        session[CSRF_SESSION_KEY] = token
    return token


def rotate_csrf_token() -> str:
    token = secrets.token_urlsafe(32)
    session[CSRF_SESSION_KEY] = token
    return token


def init_csrf(app: Flask) -> None:
    @app.before_request
    def protect_api_requests():
        if not request.path.startswith("/api/"):
            return None
        if request.method not in {"POST", "PUT", "PATCH", "DELETE"}:
            return None

        expected = session.get(CSRF_SESSION_KEY)
        supplied = request.headers.get("X-CSRF-Token", "")
        if expected and supplied and hmac.compare_digest(expected, supplied):
            return None

        return (
            jsonify(
                error={
                    "code": "CSRF_TOKEN_INVALID",
                    "message": "보안 토큰이 만료되었습니다. 페이지를 새로고침해 주세요.",
                }
            ),
            403,
        )
