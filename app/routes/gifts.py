from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from flask import Blueprint, jsonify, request
from flask_login import current_user, login_required
from sqlalchemy.exc import IntegrityError

from ..extensions import db
from ..models import ChatSession, Gift, Plant, PlantOwnership, User


gifts_bp = Blueprint("gifts", __name__, url_prefix="/api/v1")
SEOUL_TIMEZONE = ZoneInfo("Asia/Seoul")


def api_error(code: str, message: str, status: int, fields: dict | None = None):
    error = {"code": code, "message": message}
    if fields:
        error["fields"] = fields
    return jsonify(error=error), status


@gifts_bp.post("/plants/<int:plant_id>/gift")
@login_required
def give_plant(plant_id: int):
    if not request.is_json:
        return api_error("JSON_REQUIRED", "JSON 형식의 요청이 필요합니다.", 415)
    body = request.get_json(silent=True)
    if not isinstance(body, dict):
        return api_error("INVALID_REQUEST", "요청 본문을 확인해 주세요.", 400)

    recipient_nickname = str(body.get("recipientNickname", "")).strip()
    message = str(body.get("message", "")).strip() or None
    fields = {}
    if not 2 <= len(recipient_nickname) <= 50:
        fields["recipientNickname"] = "닉네임은 2자 이상 50자 이하로 입력해 주세요."
    if message and len(message) > 200:
        fields["message"] = "선물 메시지는 200자 이하로 입력해 주세요."
    if fields:
        return api_error("VALIDATION_ERROR", "입력값을 확인해 주세요.", 400, fields)

    plant = (
        Plant.query.filter_by(id=plant_id)
        .with_for_update(of=Plant)
        .first()
    )
    if not plant:
        return api_error("PLANT_NOT_FOUND", "식물을 찾을 수 없습니다.", 404)

    ownership = (
        PlantOwnership.query.filter_by(
            plant_id=plant.id,
            owner_user_id=current_user.id,
            ended_at=None,
        )
        .with_for_update()
        .first()
    )
    if not ownership:
        return api_error(
            "PLANT_OWNERSHIP_CHANGED",
            "현재 이 식물의 소유자가 아닙니다.",
            409,
        )
    if plant.growth_score < 100 or plant.status not in {"GIFT_READY", "GIFTED"}:
        return api_error(
            "PLANT_NOT_GIFT_READY",
            "완전히 성장한 식물만 선물할 수 있습니다.",
            409,
        )

    recipient = User.query.filter_by(
        nickname=recipient_nickname,
        status="ACTIVE",
    ).first()
    if not recipient:
        return api_error(
            "RECIPIENT_NOT_FOUND",
            "해당 닉네임의 사용자를 찾을 수 없습니다.",
            404,
            {"recipientNickname": "가입된 사용자의 정확한 닉네임을 입력해 주세요."},
        )
    if recipient.id == current_user.id:
        return api_error(
            "SELF_GIFT_NOT_ALLOWED",
            "자신에게는 식물을 선물할 수 없습니다.",
            409,
        )

    now = datetime.now(timezone.utc)
    gift = Gift(
        plant_id=plant.id,
        sender_user_id=current_user.id,
        recipient_user_id=recipient.id,
        recipient_name=recipient.nickname,
        gifted_on=datetime.now(SEOUL_TIMEZONE).date(),
        message_card=message,
        status="ACCEPTED",
        accepted_at=now,
    )
    db.session.add(gift)
    db.session.flush()

    ownership.ended_at = now
    new_ownership = PlantOwnership(
        plant_id=plant.id,
        owner_user_id=recipient.id,
        acquisition_type="GIFT",
        gift_id=gift.id,
    )
    db.session.add(new_ownership)
    plant.status = "GIFTED"
    ChatSession.query.filter_by(
        plant_id=plant.id,
        user_id=current_user.id,
        ended_at=None,
    ).update({"ended_at": now}, synchronize_session=False)

    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return api_error(
            "GIFT_CONFLICT",
            "식물 소유권이 변경되었습니다. 목록을 새로고침해 주세요.",
            409,
        )

    return jsonify(
        data={
            "gift": gift.to_dict(),
            "plant": plant.to_dict(new_ownership),
        }
    ), 201


@gifts_bp.post("/gifts/<int:gift_id>/acknowledge")
@login_required
def acknowledge_gift(gift_id: int):
    gift = (
        Gift.query.join(
            PlantOwnership,
            PlantOwnership.gift_id == Gift.id,
        )
        .filter(
            Gift.id == gift_id,
            Gift.recipient_user_id == current_user.id,
            PlantOwnership.owner_user_id == current_user.id,
            PlantOwnership.ended_at.is_(None),
        )
        .with_for_update()
        .first()
    )
    if not gift:
        return api_error("GIFT_NOT_FOUND", "받은 선물을 찾을 수 없습니다.", 404)

    if gift.recipient_viewed_at is None:
        gift.recipient_viewed_at = datetime.now(timezone.utc)
        db.session.commit()

    return jsonify(data={"gift": gift.to_dict()})
