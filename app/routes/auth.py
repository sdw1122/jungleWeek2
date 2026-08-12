import re

from authlib.integrations.base_client.errors import OAuthError
from flask import (
    Blueprint,
    current_app,
    jsonify,
    redirect,
    request,
    session,
    url_for,
)
from flask_login import current_user, login_required, login_user, logout_user
from requests.exceptions import RequestException
from sqlalchemy.exc import IntegrityError

from ..extensions import db, oauth
from ..models import User
from ..security import get_csrf_token, rotate_csrf_token


auth_bp = Blueprint("auth", __name__, url_prefix="/api/v1/auth")
EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class GoogleAccountError(Exception):
    def __init__(self, code: str):
        super().__init__(code)
        self.code = code


def api_error(code: str, message: str, status: int, fields: dict | None = None):
    error = {"code": code, "message": message}
    if fields:
        error["fields"] = fields
    return jsonify(error=error), status


def json_body():
    if not request.is_json:
        return None, api_error("JSON_REQUIRED", "JSON 형식의 요청이 필요합니다.", 415)
    body = request.get_json(silent=True)
    if not isinstance(body, dict):
        return None, api_error("INVALID_REQUEST", "요청 본문을 확인해 주세요.", 400)
    return body, None


@auth_bp.get("/csrf")
def csrf():
    return jsonify(data={"csrfToken": get_csrf_token()})


def _safe_next_url(value: str | None) -> str:
    if value and value.startswith("/") and not value.startswith("//"):
        return value
    return "/my-plants.html"


def _google_error_redirect(code: str):
    return redirect(url_for("main.login", oauthError=code))


def _unique_google_nickname(name: str, email: str) -> str:
    base = " ".join(name.split()).strip() or email.split("@", 1)[0]
    base = base[:50] or "Farmda 사용자"
    if len(base) < 2:
        base = f"{base}님"

    candidate = base[:50]
    suffix = 2
    while User.query.filter_by(nickname=candidate).first():
        marker = f"-{suffix}"
        candidate = f"{base[: 50 - len(marker)]}{marker}"
        suffix += 1
    return candidate


def find_or_create_google_user(userinfo: dict) -> User:
    subject = str(userinfo.get("sub", "")).strip()
    email = str(userinfo.get("email", "")).strip().lower()
    if not subject or not EMAIL_PATTERN.fullmatch(email):
        raise GoogleAccountError("invalid_profile")
    if userinfo.get("email_verified") is not True:
        raise GoogleAccountError("email_unverified")

    user = User.query.filter_by(google_subject=subject).first()
    if user:
        if not user.is_active:
            raise GoogleAccountError("account_withdrawn")
        picture = str(userinfo.get("picture", "")).strip() or None
        if picture and picture != user.profile_image_url:
            user.profile_image_url = picture
            db.session.commit()
        return user

    # 같은 이메일의 로컬 계정을 자동 연결하면 계정 탈취 위험이 있으므로 차단한다.
    if User.query.filter_by(email=email).first():
        raise GoogleAccountError("account_exists")

    user = User(
        email=email,
        nickname=_unique_google_nickname(str(userinfo.get("name", "")), email),
        auth_provider="GOOGLE",
        google_subject=subject,
        profile_image_url=str(userinfo.get("picture", "")).strip() or None,
        status="ACTIVE",
    )
    db.session.add(user)
    try:
        db.session.commit()
    except IntegrityError as error:
        db.session.rollback()
        raise GoogleAccountError("account_exists") from error
    return user


@auth_bp.get("/google")
def google_login():
    if current_user.is_authenticated:
        return redirect(_safe_next_url(request.args.get("next")))
    if not current_app.config.get("GOOGLE_CLIENT_ID") or not current_app.config.get(
        "GOOGLE_CLIENT_SECRET"
    ):
        return _google_error_redirect("not_configured")

    session["google_oauth_next"] = _safe_next_url(request.args.get("next"))
    redirect_uri = url_for("auth.google_callback", _external=True)
    return oauth.google.authorize_redirect(redirect_uri)


@auth_bp.get("/google/callback")
def google_callback():
    if request.args.get("error"):
        return _google_error_redirect("cancelled")

    try:
        token = oauth.google.authorize_access_token()
        userinfo = token["userinfo"]
    except (OAuthError, RequestException, KeyError, TypeError, ValueError):
        current_app.logger.exception("Google OAuth callback failed")
        return _google_error_redirect("oauth_failed")

    try:
        user = find_or_create_google_user(dict(userinfo))
    except GoogleAccountError as error:
        return _google_error_redirect(error.code)

    destination = _safe_next_url(session.get("google_oauth_next"))
    session.clear()
    login_user(user)
    rotate_csrf_token()
    return redirect(destination)


@auth_bp.post("/signup")
def signup():
    body, error = json_body()
    if error:
        return error

    nickname = str(body.get("nickname", "")).strip()
    email = str(body.get("email", "")).strip().lower()
    password = body.get("password")
    fields = {}

    if not 2 <= len(nickname) <= 50:
        fields["nickname"] = "닉네임은 2자 이상 50자 이하로 입력해 주세요."
    if len(email) > 255 or not EMAIL_PATTERN.fullmatch(email):
        fields["email"] = "올바른 이메일 주소를 입력해 주세요."
    if not isinstance(password, str) or not 8 <= len(password) <= 128:
        fields["password"] = "비밀번호는 8자 이상 128자 이하로 입력해 주세요."
    if fields:
        return api_error("VALIDATION_ERROR", "입력값을 확인해 주세요.", 400, fields)

    if User.query.filter_by(email=email).first():
        return api_error("EMAIL_ALREADY_EXISTS", "이미 가입된 이메일입니다.", 409)
    if User.query.filter_by(nickname=nickname).first():
        return api_error("NICKNAME_ALREADY_EXISTS", "이미 사용 중인 닉네임입니다.", 409)

    user = User(
        email=email,
        nickname=nickname,
        auth_provider="LOCAL",
        status="ACTIVE",
    )
    user.set_password(password)
    db.session.add(user)
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return api_error(
            "ACCOUNT_ALREADY_EXISTS",
            "이미 가입된 이메일 또는 닉네임입니다.",
            409,
        )

    return jsonify(data={"user": user.to_dict()}), 201


@auth_bp.post("/login")
def login():
    body, error = json_body()
    if error:
        return error

    email = str(body.get("email", "")).strip().lower()
    password = body.get("password")
    remember = body.get("remember", False)
    if not isinstance(password, str) or not isinstance(remember, bool):
        return api_error(
            "VALIDATION_ERROR",
            "이메일과 비밀번호를 확인해 주세요.",
            400,
        )

    user = User.query.filter_by(email=email).first()
    if not user or not user.is_active or not user.check_password(password):
        return api_error(
            "INVALID_CREDENTIALS",
            "이메일 또는 비밀번호가 올바르지 않습니다.",
            401,
        )

    session.clear()
    login_user(user, remember=remember)
    csrf_token = rotate_csrf_token()
    return jsonify(data={"user": user.to_dict(), "csrfToken": csrf_token})


@auth_bp.post("/logout")
@login_required
def logout():
    logout_user()
    remember_operation = session.get("_remember")
    session.clear()
    if remember_operation == "clear":
        session["_remember"] = "clear"
    csrf_token = rotate_csrf_token()
    return jsonify(
        data={"message": "로그아웃되었습니다.", "csrfToken": csrf_token}
    )


@auth_bp.get("/me")
@login_required
def me():
    return jsonify(data={"user": current_user.to_dict()})

