from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from ..extensions import db
from ..models.guestbook import GuestbookEntry, GuestbookReply, GuestbookReaction, GuestbookReplyReaction

guestbook_bp = Blueprint("guestbook_api", __name__, url_prefix="/api/guestbook")

@guestbook_bp.get("/")
def get_guestbooks():
    """방명록 전체 조회"""
    entries = GuestbookEntry.query.order_by(GuestbookEntry.created_at.desc()).all()
    return jsonify(status="success", data=[entry.to_dict() for entry in entries]), 200

@guestbook_bp.post("/")
@login_required
def create_guestbook():
    """방명록 작성"""
    data = request.get_json() or {}
    content = data.get("content")
    
    if not content:
        return jsonify(status="error", message="내용이 비어있습니다."), 400
        
    new_entry = GuestbookEntry(
        author_id=current_user.id,
        content=content
    )
    db.session.add(new_entry)
    db.session.commit()
    
    return jsonify(status="success", data=new_entry.to_dict()), 201

@guestbook_bp.put("/<int:entry_id>")
@login_required
def update_guestbook(entry_id):
    """내가 작성한 방명록 수정"""
    entry = db.session.get(GuestbookEntry, entry_id)
    if not entry:
        return jsonify(status="error", message="방명록을 찾을 수 없습니다."), 404

    if entry.author_id != current_user.id:
        return jsonify(status="error", message="본인의 글만 수정할 수 있습니다."), 403

    data = request.get_json() or {}
    new_content = data.get("content")
    
    if not new_content:
        return jsonify(status="error", message="수정할 내용이 비어있습니다."), 400
        
    entry.content = new_content
    db.session.commit()
    
    return jsonify(status="success", data=entry.to_dict()), 200

@guestbook_bp.delete("/<int:entry_id>")
@login_required
def delete_guestbook(entry_id):
    """내가 작성한 방명록 삭제"""
    entry = db.session.get(GuestbookEntry, entry_id)
    if not entry:
        return jsonify(status="error", message="방명록을 찾을 수 없습니다."), 404
        
    if entry.author_id != current_user.id:
        return jsonify(status="error", message="본인의 글만 삭제할 수 있습니다."), 403

    db.session.delete(entry)
    db.session.commit()
    
    return jsonify(status="success", message="삭제되었습니다."), 200

@guestbook_bp.post("/<int:entry_id>/reaction")
@login_required
def add_reaction(entry_id):
    """본문 리액션 (좋아요/싫어요) 토글"""
    entry = db.session.get(GuestbookEntry, entry_id)
    if not entry:
        return jsonify(status="error", message="방명록을 찾을 수 없습니다."), 404

    data = request.get_json() or {}
    reaction_type = data.get("type")

    if reaction_type not in ("like", "dislike"):
        return jsonify(status="error", message="유효하지 않은 리액션 타입입니다."), 400

    existing_reaction = GuestbookReaction.query.filter_by(entry_id=entry_id, user_id=current_user.id).first()
    
    if existing_reaction:
        if existing_reaction.reaction_type == reaction_type:
            # Same reaction -> toggle off
            db.session.delete(existing_reaction)
        else:
            # Different reaction -> switch
            existing_reaction.reaction_type = reaction_type
    else:
        # No reaction -> add new
        new_reaction = GuestbookReaction(entry_id=entry_id, user_id=current_user.id, reaction_type=reaction_type)
        db.session.add(new_reaction)

    db.session.commit()
    
    # Refresh entry to get updated relationships
    return jsonify(status="success", data={"reactions": entry.to_dict()["reactions"]}), 200

@guestbook_bp.post("/<int:entry_id>/reply")
@login_required
def add_reply(entry_id):
    """답글(대댓글) 작성"""
    entry = db.session.get(GuestbookEntry, entry_id)
    if not entry:
        return jsonify(status="error", message="방명록을 찾을 수 없습니다."), 404

    data = request.get_json() or {}
    content = data.get("content")

    if not content:
        return jsonify(status="error", message="답글 내용이 비어있습니다."), 400

    new_reply = GuestbookReply(
        entry_id=entry_id,
        author_id=current_user.id,
        content=content
    )
    db.session.add(new_reply)
    db.session.commit()

    return jsonify(status="success", data={"replies": entry.to_dict()["replies"]}), 201

@guestbook_bp.post("/reply/<int:reply_id>/reaction")
@login_required
def add_reply_reaction(reply_id):
    """답글 리액션 (좋아요/싫어요) 토글"""
    reply = db.session.get(GuestbookReply, reply_id)
    if not reply:
        return jsonify(status="error", message="답글을 찾을 수 없습니다."), 404

    data = request.get_json() or {}
    reaction_type = data.get("type")

    if reaction_type not in ("like", "dislike"):
        return jsonify(status="error", message="유효하지 않은 리액션 타입입니다."), 400

    existing_reaction = GuestbookReplyReaction.query.filter_by(reply_id=reply_id, user_id=current_user.id).first()
    
    if existing_reaction:
        if existing_reaction.reaction_type == reaction_type:
            db.session.delete(existing_reaction)
        else:
            existing_reaction.reaction_type = reaction_type
    else:
        new_reaction = GuestbookReplyReaction(reply_id=reply_id, user_id=current_user.id, reaction_type=reaction_type)
        db.session.add(new_reaction)

    db.session.commit()
    
    return jsonify(status="success", data={"reactions": reply.to_dict()["reactions"]}), 200

