from flask import Blueprint, request, jsonify

guestbook_bp = Blueprint("guestbook_api", __name__, url_prefix="/api/guestbook")

# 임시 메모리 DB (Mock)
mock_db = {
    1: {"id": 1, "content": "식물이 너무 예뻐요!", "author": "지나가던 요정", "reactions": {"like": 0, "dislike": 0}, "replies": []}
}
next_id = 2

@guestbook_bp.get("/")
def get_guestbooks():
    """방명록 전체 조회 (원래 기능)"""
    return jsonify(status="success", data=list(mock_db.values())), 200

@guestbook_bp.post("/")
def create_guestbook():
    """닉네임으로 방명록 작성 (원래 기능)"""
    global next_id
    data = request.get_json() or {}
    content = data.get("content")
    author = data.get("author", "익명")
    
    if not content:
        return jsonify(status="error", message="내용이 비어있습니다."), 400
        
    new_entry = {
        "id": next_id,
        "content": content,
        "author": author,
        "reactions": {"like": 0, "dislike": 0},
        "replies": []
    }
    mock_db[next_id] = new_entry
    next_id += 1
    
    return jsonify(status="success", data=new_entry), 201

@guestbook_bp.put("/<int:entry_id>")
def update_guestbook(entry_id):
    """내가 작성한 방명록 수정 (추가 요청)"""
    entry = mock_db.get(entry_id)
    if not entry:
        return jsonify(status="error", message="방명록을 찾을 수 없습니다."), 404

    data = request.get_json() or {}
    new_content = data.get("content")
    
    if not new_content:
        return jsonify(status="error", message="수정할 내용이 비어있습니다."), 400
        
    # 실제 환경에서는 작성자 본인인지(혹은 비밀번호 일치하는지) 확인하는 로직 필요
    entry["content"] = new_content
    
    return jsonify(status="success", data=entry), 200

@guestbook_bp.delete("/<int:entry_id>")
def delete_guestbook(entry_id):
    """내가 작성한 방명록 삭제 (원래 기능)"""
    if entry_id not in mock_db:
        return jsonify(status="error", message="방명록을 찾을 수 없습니다."), 404
        
    # 실제 환경에서는 작성자 본인인지 확인하는 로직 필요
    del mock_db[entry_id]
    
    return jsonify(status="success", message="삭제되었습니다."), 200

@guestbook_bp.post("/<int:entry_id>/reaction")
def add_reaction(entry_id):
    """3. 스탬프/리액션 달기 기능 (새로운 기능)"""
    entry = mock_db.get(entry_id)
    if not entry:
        return jsonify(status="error", message="방명록을 찾을 수 없습니다."), 404

    data = request.get_json() or {}
    reaction_type = data.get("type")

    if reaction_type not in entry["reactions"]:
        return jsonify(status="error", message="유효하지 않은 리액션 타입입니다."), 400

    entry["reactions"][reaction_type] += 1
    
    return jsonify(status="success", data={"reactions": entry["reactions"]}), 200

@guestbook_bp.post("/<int:entry_id>/reply")
def add_reply(entry_id):
    """4. 주인장 답글(대댓글) 기능 (새로운 기능)"""
    entry = mock_db.get(entry_id)
    if not entry:
        return jsonify(status="error", message="방명록을 찾을 수 없습니다."), 404

    data = request.get_json() or {}
    content = data.get("content")

    if not content:
        return jsonify(status="error", message="답글 내용이 비어있습니다."), 400

    new_reply = {
        "author": data.get("author", "익명"), 
        "content": content
    }
    
    entry["replies"].append(new_reply)

    return jsonify(status="success", data={"replies": entry["replies"]}), 201

