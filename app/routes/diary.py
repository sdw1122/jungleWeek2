from __future__ import annotations

from collections import OrderedDict
from datetime import date, datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo

from flask import Blueprint, jsonify, request
from flask_login import current_user, login_required
from sqlalchemy.exc import IntegrityError

from ..extensions import db
from ..models import (
    CareLog,
    ChatMessage,
    ChatSession,
    DiaryEntry,
    Plant,
    PlantOwnership,
)
from ..services.diary_service import generate_diary_draft


diary_bp = Blueprint("diary", __name__, url_prefix="/api/v1")
SEOUL_TIMEZONE = ZoneInfo("Asia/Seoul")
ACTION_LABELS = {
    "WATER": "물 주기",
    "SUNLIGHT": "햇빛 쬐어주기",
    "PET": "쓰다듬기",
    "IGNORE": "방치하기",
}


def api_error(code: str, message: str, status: int, fields: dict | None = None):
    error = {"code": code, "message": message}
    if fields:
        error["fields"] = fields
    return jsonify(error=error), status


def _seoul_today() -> date:
    return datetime.now(SEOUL_TIMEZONE).date()


def _utc_day_bounds(day: date) -> tuple[datetime, datetime]:
    start_local = datetime.combine(day, time.min, tzinfo=SEOUL_TIMEZONE)
    end_local = start_local + timedelta(days=1)
    return start_local.astimezone(timezone.utc), end_local.astimezone(timezone.utc)


def _active_ownership(plant_id: int, user_id: int):
    return PlantOwnership.query.filter_by(
        plant_id=plant_id,
        owner_user_id=user_id,
        ended_at=None,
    ).first()


def _access_type(plant_id: int) -> tuple[str | None, PlantOwnership | None]:
    ownership = _active_ownership(plant_id, current_user.id)
    if ownership:
        return "OWNER", ownership
    authored = DiaryEntry.query.filter_by(
        plant_id=plant_id,
        author_user_id=current_user.id,
    ).first()
    return ("AUTHOR_ARCHIVE", None) if authored else (None, None)


def _visible_entries_query(plant_id: int, access_type: str):
    query = DiaryEntry.query.filter_by(plant_id=plant_id)
    if access_type != "OWNER":
        query = query.filter_by(author_user_id=current_user.id)
    return query


def _text_fields(body: dict):
    title = " ".join(str(body.get("title", "")).split()).strip()
    content = str(body.get("content", "")).strip()
    fields = {}
    if not 1 <= len(title) <= 150:
        fields["title"] = "제목은 1자 이상 150자 이하로 입력해 주세요."
    if not 1 <= len(content) <= 2000:
        fields["content"] = "내용은 1자 이상 2,000자 이하로 입력해 주세요."
    return title, content, fields


def _collect_activity(plant_id: int, day: date) -> tuple[dict, list[dict], str | None]:
    start_utc, end_utc = _utc_day_bounds(day)
    care_logs = (
        CareLog.query.filter(
            CareLog.plant_id == plant_id,
            CareLog.created_at >= start_utc,
            CareLog.created_at < end_utc,
        )
        .order_by(CareLog.created_at, CareLog.id)
        .all()
    )
    grouped: OrderedDict[str, dict] = OrderedDict()
    for log in care_logs:
        item = grouped.setdefault(
            log.action_type,
            {
                "actionType": log.action_type,
                "label": ACTION_LABELS.get(log.action_type, log.action_type),
                "count": 0,
                "growthDelta": 0,
                "positiveDelta": 0,
                "negativeDelta": 0,
            },
        )
        item["count"] += 1
        item["growthDelta"] += log.growth_delta
        item["positiveDelta"] += log.positive_delta
        item["negativeDelta"] += log.negative_delta

    chat_rows = (
        ChatMessage.query.join(ChatSession, ChatSession.id == ChatMessage.session_id)
        .filter(
            ChatSession.plant_id == plant_id,
            ChatMessage.created_at >= start_utc,
            ChatMessage.created_at < end_utc,
        )
        .order_by(ChatMessage.created_at, ChatMessage.id)
        .all()
    )
    recent_messages = [
        {"role": item.role, "content": item.content}
        for item in chat_rows[-20:]
    ]
    representative = next(
        (item.content for item in reversed(chat_rows) if item.role == "USER"),
        None,
    )
    chat_positive = sum(item.positive_delta for item in chat_rows)
    chat_negative = sum(item.negative_delta for item in chat_rows)
    care_growth = sum(item["growthDelta"] for item in grouped.values())
    care_positive = sum(item["positiveDelta"] for item in grouped.values())
    care_negative = sum(item["negativeDelta"] for item in grouped.values())
    summary = {
        "careActions": list(grouped.values()),
        "chat": {
            "messageCount": len(chat_rows),
            "positiveDelta": chat_positive,
            "negativeDelta": chat_negative,
            "representativeMessage": representative,
        },
        "totals": {
            "growthDelta": care_growth,
            "positiveDelta": care_positive + chat_positive,
            "negativeDelta": care_negative + chat_negative,
        },
    }
    latest_care_action = care_logs[-1].action_type if care_logs else None
    return summary, recent_messages, latest_care_action


def _apply_snapshot(entry: DiaryEntry, plant: Plant, summary: dict) -> None:
    entry.mood_snapshot = plant.mood
    entry.growth_score_snapshot = plant.growth_score
    entry.positive_energy_snapshot = plant.positive_energy
    entry.negative_energy_snapshot = plant.negative_energy
    entry.growth_stage_snapshot = plant.growth_stage
    entry.growth_tendency_snapshot = (
        "NEGATIVE" if plant.negative_energy > plant.positive_energy else "POSITIVE"
    )
    entry.activity_summary = summary
    entry.is_public = False


def _entry_can_edit(entry: DiaryEntry) -> bool:
    return (
        entry.author_user_id == current_user.id
        or _active_ownership(entry.plant_id, current_user.id) is not None
    )


@diary_bp.get("/diary/plants")
@login_required
def accessible_plants():
    rows = (
        db.session.query(Plant, PlantOwnership)
        .join(PlantOwnership, PlantOwnership.plant_id == Plant.id)
        .filter(
            PlantOwnership.owner_user_id == current_user.id,
            PlantOwnership.ended_at.is_(None),
        )
        .order_by(PlantOwnership.started_at.desc(), Plant.id.desc())
        .all()
    )
    result = []
    owned_ids = set()
    for plant, ownership in rows:
        owned_ids.add(plant.id)
        item = plant.to_dict(ownership)
        item["accessType"] = "OWNER"
        result.append(item)

    archived_ids = [
        row[0]
        for row in db.session.query(DiaryEntry.plant_id)
        .filter(DiaryEntry.author_user_id == current_user.id)
        .distinct()
        .all()
        if row[0] not in owned_ids
    ]
    if archived_ids:
        archived_plants = (
            Plant.query.filter(Plant.id.in_(archived_ids))
            .order_by(Plant.id.desc())
            .all()
        )
        for plant in archived_plants:
            item = plant.to_dict()
            item["accessType"] = "AUTHOR_ARCHIVE"
            result.append(item)
    return jsonify(data={"plants": result})


@diary_bp.get("/plants/<int:plant_id>/diary")
@login_required
def monthly_diary(plant_id: int):
    plant = db.session.get(Plant, plant_id)
    access_type, ownership = _access_type(plant_id)
    if not plant or not access_type:
        return api_error("DIARY_ACCESS_DENIED", "성장일기를 볼 수 없습니다.", 404)

    today = _seoul_today()
    try:
        year = int(request.args.get("year", today.year))
        month = int(request.args.get("month", today.month))
        month_start = date(year, month, 1)
    except (TypeError, ValueError):
        return api_error("INVALID_MONTH", "조회할 연도와 월을 확인해 주세요.", 400)
    if not 2000 <= year <= 2100:
        return api_error("INVALID_MONTH", "조회할 연도와 월을 확인해 주세요.", 400)
    month_end = (
        date(year + 1, 1, 1) if month == 12 else date(year, month + 1, 1)
    )

    base_query = _visible_entries_query(plant_id, access_type)
    entries = (
        base_query.filter(
            DiaryEntry.diary_date >= month_start,
            DiaryEntry.diary_date < month_end,
        )
        .order_by(DiaryEntry.diary_date)
        .all()
    )
    recent = (
        _visible_entries_query(plant_id, access_type)
        .order_by(DiaryEntry.diary_date.desc(), DiaryEntry.id.desc())
        .limit(3)
        .all()
    )
    positive_count = sum(
        entry.growth_tendency_snapshot == "POSITIVE" for entry in entries
    )
    negative_count = len(entries) - positive_count
    net_energy = sum(
        int((entry.activity_summary or {}).get("totals", {}).get("positiveDelta", 0))
        - int((entry.activity_summary or {}).get("totals", {}).get("negativeDelta", 0))
        for entry in entries
    )
    plant_data = plant.to_dict(ownership)
    plant_data["accessType"] = access_type
    return jsonify(
        data={
            "plant": plant_data,
            "entries": [
                entry.to_dict(can_edit=_entry_can_edit(entry), include_content=False)
                for entry in entries
            ],
            "recentEntries": [
                entry.to_dict(can_edit=_entry_can_edit(entry), include_content=False)
                for entry in recent
            ],
            "summary": {
                "entryCount": len(entries),
                "positiveCount": positive_count,
                "negativeCount": negative_count,
                "netEnergy": net_energy,
            },
            "today": today.isoformat(),
        }
    )


@diary_bp.get("/diary/<int:entry_id>")
@login_required
def diary_detail(entry_id: int):
    entry = db.session.get(DiaryEntry, entry_id)
    if not entry:
        return api_error("DIARY_NOT_FOUND", "성장일기를 찾을 수 없습니다.", 404)
    access_type, _ = _access_type(entry.plant_id)
    if not access_type or (
        access_type != "OWNER" and entry.author_user_id != current_user.id
    ):
        return api_error("DIARY_NOT_FOUND", "성장일기를 찾을 수 없습니다.", 404)
    return jsonify(data={"entry": entry.to_dict(can_edit=_entry_can_edit(entry))})


@diary_bp.post("/plants/<int:plant_id>/diary/draft")
@login_required
def diary_draft(plant_id: int):
    plant = db.session.get(Plant, plant_id)
    if not plant or not _active_ownership(plant_id, current_user.id):
        return api_error(
            "PLANT_OWNERSHIP_REQUIRED",
            "현재 소유한 식물만 성장일기를 만들 수 있습니다.",
            403,
        )
    today = _seoul_today()
    summary, messages, latest_care = _collect_activity(plant.id, today)
    draft = generate_diary_draft(
        plant_name=plant.display_name,
        mood=plant.mood,
        growth_score=plant.growth_score,
        positive_energy=plant.positive_energy,
        negative_energy=plant.negative_energy,
        latest_care_action=latest_care,
        activity_summary=summary,
        recent_messages=messages,
    )
    return jsonify(
        data={
            "draft": {
                "title": draft["title"],
                "content": draft["content"],
                "fallback": draft["fallback"],
                "diaryDate": today.isoformat(),
                "activitySummary": summary,
            }
        }
    )


@diary_bp.put("/plants/<int:plant_id>/diary/today")
@login_required
def save_today_diary(plant_id: int):
    if not request.is_json:
        return api_error("JSON_REQUIRED", "JSON 형식의 요청이 필요합니다.", 415)
    body = request.get_json(silent=True)
    if not isinstance(body, dict):
        return api_error("INVALID_REQUEST", "요청 본문을 확인해 주세요.", 400)
    title, content, fields = _text_fields(body)
    if fields:
        return api_error("VALIDATION_ERROR", "입력값을 확인해 주세요.", 400, fields)

    plant = Plant.query.filter_by(id=plant_id).with_for_update(of=Plant).first()
    ownership = _active_ownership(plant_id, current_user.id) if plant else None
    if not plant or not ownership:
        return api_error(
            "PLANT_OWNERSHIP_REQUIRED",
            "현재 소유한 식물만 성장일기를 저장할 수 있습니다.",
            403,
        )
    today = _seoul_today()
    entry = (
        DiaryEntry.query.filter_by(plant_id=plant.id, diary_date=today)
        .with_for_update()
        .first()
    )
    summary, _, _ = _collect_activity(plant.id, today)
    created = entry is None
    if created:
        entry = DiaryEntry(
            plant_id=plant.id,
            author_user_id=current_user.id,
            diary_date=today,
            source_type="AI",
            title=title,
            content=content,
        )
        db.session.add(entry)
    else:
        entry.title = title
        entry.content = content

    _apply_snapshot(entry, plant, summary)
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return api_error(
            "DIARY_CONFLICT",
            "오늘의 일기가 이미 저장되었습니다. 새로고침 후 다시 시도해 주세요.",
            409,
        )
    return (
        jsonify(data={"entry": entry.to_dict(can_edit=True)}),
        201 if created else 200,
    )


@diary_bp.patch("/diary/<int:entry_id>")
@login_required
def update_diary(entry_id: int):
    if not request.is_json:
        return api_error("JSON_REQUIRED", "JSON 형식의 요청이 필요합니다.", 415)
    body = request.get_json(silent=True)
    if not isinstance(body, dict):
        return api_error("INVALID_REQUEST", "요청 본문을 확인해 주세요.", 400)
    title, content, fields = _text_fields(body)
    if fields:
        return api_error("VALIDATION_ERROR", "입력값을 확인해 주세요.", 400, fields)

    entry = DiaryEntry.query.filter_by(id=entry_id).with_for_update().first()
    if not entry:
        return api_error("DIARY_NOT_FOUND", "성장일기를 찾을 수 없습니다.", 404)
    if not _entry_can_edit(entry):
        return api_error("DIARY_EDIT_FORBIDDEN", "성장일기 수정 권한이 없습니다.", 403)
    entry.title = title
    entry.content = content
    db.session.commit()
    return jsonify(data={"entry": entry.to_dict(can_edit=True)})
