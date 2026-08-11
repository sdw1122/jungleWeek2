from flask import Blueprint, jsonify, request
from flask_login import current_user, login_required

from ..extensions import db
from ..models import CareLog, ChatMessage, ChatSession, Plant, PlantOwnership
from ..services.ai_service import analyze_chat


chat_bp = Blueprint("chat", __name__, url_prefix="/api/chat")


def api_error(code: str, message: str, status: int):
    return jsonify(error={"code": code, "message": message}), status


def owned_plant(plant_id: int):
    return (
        db.session.query(Plant, PlantOwnership)
        .join(PlantOwnership, PlantOwnership.plant_id == Plant.id)
        .filter(
            Plant.id == plant_id,
            PlantOwnership.owner_user_id == current_user.id,
            PlantOwnership.ended_at.is_(None),
        )
        .first()
    )


@chat_bp.post("")
@login_required
def chat():
    if not request.is_json:
        return api_error("JSON_REQUIRED", "JSON 형식의 요청이 필요합니다.", 415)

    body = request.get_json(silent=True)
    if not isinstance(body, dict):
        return api_error("INVALID_REQUEST", "요청 본문을 확인해 주세요.", 400)

    message = " ".join(str(body.get("message", "")).split()).strip()
    try:
        plant_id = int(body.get("plant_id"))
    except (TypeError, ValueError):
        plant_id = 0

    if not 1 <= len(message) <= 120 or plant_id < 1:
        return api_error(
            "VALIDATION_ERROR",
            "식물과 1자 이상 120자 이하의 메시지를 확인해 주세요.",
            400,
        )

    row = owned_plant(plant_id)
    if not row:
        return api_error("PLANT_NOT_FOUND", "식물을 찾을 수 없습니다.", 404)
    plant, ownership = row

    session = ChatSession.query.filter_by(
        plant_id=plant.id,
        user_id=current_user.id,
        ended_at=None,
    ).first()
    if not session:
        session = ChatSession(plant_id=plant.id, user_id=current_user.id)
        db.session.add(session)
        db.session.flush()

    past_messages = (
        ChatMessage.query.filter_by(session_id=session.id)
        .order_by(ChatMessage.created_at.desc(), ChatMessage.id.desc())
        .limit(10)
        .all()
    )
    history = [
        {"role": item.role, "content": item.content}
        for item in reversed(past_messages)
    ]
    latest_care = (
        CareLog.query.filter_by(plant_id=plant.id)
        .order_by(CareLog.created_at.desc(), CareLog.id.desc())
        .first()
    )
    ai_result = analyze_chat(
        message,
        history,
        plant.positive_energy,
        plant.negative_energy,
        plant.growth_score,
        latest_care.action_type if latest_care else None,
    )

    sentiment = str(ai_result.get("sentiment", "NEUTRAL")).upper()
    if sentiment not in {"POSITIVE", "NEGATIVE", "NEUTRAL"}:
        sentiment = "NEUTRAL"
    response_text = str(ai_result.get("response", "잠시 후 다시 말해 주세요."))[:2000]
    emotion = str(ai_result.get("emotion", "평온"))[:30]
    positive_delta = min(5, max(0, int(ai_result.get("positive_delta", 0) or 0)))
    negative_delta = min(5, max(0, int(ai_result.get("negative_delta", 0) or 0)))

    db.session.add(ChatMessage(session_id=session.id, role="USER", content=message))
    db.session.add(
        ChatMessage(
            session_id=session.id,
            role="PLANT",
            content=response_text,
            positive_delta=positive_delta,
            negative_delta=negative_delta,
        )
    )

    plant.positive_energy += positive_delta
    plant.negative_energy += negative_delta
    plant.mood = emotion
    db.session.commit()

    return jsonify(
        response=response_text,
        sentiment=sentiment,
        emotion=emotion,
        positiveDelta=positive_delta,
        negativeDelta=negative_delta,
        plant=plant.to_dict(ownership),
    )
