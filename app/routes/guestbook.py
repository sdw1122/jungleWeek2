from flask import Blueprint, jsonify, request
from flask_login import current_user, login_required

from ..extensions import db
from ..models.guestbook import (
    GuestbookEntry,
    GuestbookReaction,
    GuestbookReply,
    GuestbookReplyReaction,
)


guestbook_bp = Blueprint("guestbook", __name__, url_prefix="/api/v1/guestbook")


def error_response(code: str, message: str, status: int):
    return jsonify(error={"code": code, "message": message}), status


def content_from_request():
    if not request.is_json:
        return None, error_response("JSON_REQUIRED", "JSON 형식의 요청이 필요합니다.", 415)
    body = request.get_json(silent=True)
    if not isinstance(body, dict):
        return None, error_response("INVALID_REQUEST", "요청 본문을 확인해 주세요.", 400)
    content = str(body.get("content", "")).strip()
    if not 1 <= len(content) <= 500:
        return None, error_response(
            "VALIDATION_FAILED", "내용은 1자 이상 500자 이하로 입력해 주세요.", 400
        )
    return content, None


def reaction_type_from_request():
    body = request.get_json(silent=True) if request.is_json else None
    reaction_type = str((body or {}).get("type", "")).strip().lower()
    if reaction_type not in {"like", "dislike"}:
        return None, error_response(
            "INVALID_REACTION", "좋아요 또는 싫어요를 선택해 주세요.", 400
        )
    return reaction_type, None


@guestbook_bp.get("")
@guestbook_bp.get("/")
def get_entries():
    entries = GuestbookEntry.query.order_by(
        GuestbookEntry.created_at.desc(), GuestbookEntry.id.desc()
    ).all()
    return jsonify(status="success", data=[entry.to_dict() for entry in entries])


@guestbook_bp.post("")
@guestbook_bp.post("/")
@login_required
def create_entry():
    content, error = content_from_request()
    if error:
        return error
    entry = GuestbookEntry(
        author_user_id=current_user.id,
        nickname_snapshot=current_user.nickname,
        content=content,
    )
    db.session.add(entry)
    db.session.commit()
    return jsonify(status="success", data=entry.to_dict()), 201


@guestbook_bp.put("/<int:entry_id>")
@login_required
def update_entry(entry_id: int):
    entry = db.session.get(GuestbookEntry, entry_id)
    if not entry:
        return error_response("NOT_FOUND", "방명록을 찾을 수 없습니다.", 404)
    if entry.author_user_id != current_user.id:
        return error_response("FORBIDDEN", "본인의 글만 수정할 수 있습니다.", 403)
    content, error = content_from_request()
    if error:
        return error
    entry.content = content
    db.session.commit()
    return jsonify(status="success", data=entry.to_dict())


@guestbook_bp.delete("/<int:entry_id>")
@login_required
def delete_entry(entry_id: int):
    entry = db.session.get(GuestbookEntry, entry_id)
    if not entry:
        return error_response("NOT_FOUND", "방명록을 찾을 수 없습니다.", 404)
    if entry.author_user_id != current_user.id:
        return error_response("FORBIDDEN", "본인의 글만 삭제할 수 있습니다.", 403)
    db.session.delete(entry)
    db.session.commit()
    return jsonify(status="success", message="삭제되었습니다.")


def toggle_reaction(model, **target):
    reaction_type, error = reaction_type_from_request()
    if error:
        return None, error
    reaction = model.query.filter_by(user_id=current_user.id, **target).first()
    if reaction and reaction.reaction_type == reaction_type:
        db.session.delete(reaction)
    elif reaction:
        reaction.reaction_type = reaction_type
    else:
        db.session.add(
            model(user_id=current_user.id, reaction_type=reaction_type, **target)
        )
    db.session.commit()
    return reaction_type, None


@guestbook_bp.post("/<int:entry_id>/reaction")
@login_required
def react_to_entry(entry_id: int):
    entry = db.session.get(GuestbookEntry, entry_id)
    if not entry:
        return error_response("NOT_FOUND", "방명록을 찾을 수 없습니다.", 404)
    _, error = toggle_reaction(GuestbookReaction, entry_id=entry.id)
    if error:
        return error
    return jsonify(status="success", data={"reactions": entry.to_dict()["reactions"]})


@guestbook_bp.post("/<int:entry_id>/reply")
@login_required
def create_reply(entry_id: int):
    entry = db.session.get(GuestbookEntry, entry_id)
    if not entry:
        return error_response("NOT_FOUND", "방명록을 찾을 수 없습니다.", 404)
    content, error = content_from_request()
    if error:
        return error
    reply = GuestbookReply(
        entry_id=entry.id,
        author_user_id=current_user.id,
        nickname_snapshot=current_user.nickname,
        content=content,
    )
    db.session.add(reply)
    db.session.commit()
    return jsonify(status="success", data={"replies": entry.to_dict()["replies"]}), 201


@guestbook_bp.post("/reply/<int:reply_id>/reaction")
@login_required
def react_to_reply(reply_id: int):
    reply = db.session.get(GuestbookReply, reply_id)
    if not reply:
        return error_response("NOT_FOUND", "답글을 찾을 수 없습니다.", 404)
    _, error = toggle_reaction(GuestbookReplyReaction, reply_id=reply.id)
    if error:
        return error
    return jsonify(status="success", data={"reactions": reply.to_dict()["reactions"]})
