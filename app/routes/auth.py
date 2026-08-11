import re

from flask import Blueprint, jsonify, request, session
from flask_login import current_user, login_required, login_user, logout_user
from sqlalchemy.exc import IntegrityError

from ..extensions import db
from ..models import User
from ..security import get_csrf_token, rotate_csrf_token


auth_bp = Blueprint("auth", __name__, url_prefix="/api/v1/auth")

EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def api_error(code: str, message: str, status: int, fields: dict | None = None):
    error = {"code": code, "message": message}
    if fields:
        error["fields"] = fields
    return jsonify(error=error), status


def json_body():
    if not request.is_json:
        return None, api_error(
            "JSON_REQUIRED",
            "JSON 형식의 요청이 필요합니다.",
            415,
        )
    body = request.get_json(silent=True)
    if not isinstance(body, dict):
        return None, api_error(
            "INVALID_REQUEST",
            "요청 본문을 확인해 주세요.",
            400,
        )
    return body, None


@auth_bp.get("/csrf")
def csrf():
    return jsonify(data={"csrfToken": get_csrf_token()})


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
        return api_error(
            "VALIDATION_ERROR",
            "입력값을 확인해 주세요.",
            400,
            fields,
        )

    if User.query.filter_by(email=email).first():
        return api_error(
            "EMAIL_ALREADY_EXISTS",
            "이미 가입된 이메일입니다.",
            409,
        )
    if User.query.filter_by(nickname=nickname).first():
        return api_error(
            "NICKNAME_ALREADY_EXISTS",
            "이미 사용 중인 닉네임입니다.",
            409,
        )

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
