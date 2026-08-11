from flask import Blueprint, request, jsonify
from flask_login import current_user
from ..extensions import db
from ..models.guestbook import GuestbookEntry

guestbook_bp = Blueprint('guestbook', __name__, url_prefix='/api/v1/guestbook')

def error_response(code, message, status_code, fields=None):
    err = {'code': code, 'message': message}
    if fields:
        err['fields'] = fields
    return jsonify({'error': err}), status_code

@guestbook_bp.route('', methods=['GET'])
def get_entries():
    entries = GuestbookEntry.query.order_by(GuestbookEntry.created_at.desc()).all()
    return jsonify({'status': 'success', 'data': [entry.to_dict() for entry in entries]})

@guestbook_bp.route('', methods=['POST'])
def create_entry():
    if not current_user.is_authenticated:
        return error_response('UNAUTHORIZED', '로그인이 필요합니다.', 401)
        
    data = request.get_json() or {}
    content = data.get('content')
    
    if not content or not content.strip():
        return error_response('VALIDATION_FAILED', '내용을 입력해주세요.', 400, {'content': 'Required'})
        
    entry = GuestbookEntry(
        author_user_id=current_user.id,
        nickname_snapshot=current_user.nickname,
        content=content.strip()
    )
    
    db.session.add(entry)
    db.session.commit()
    
    return jsonify({'status': 'success', 'data': entry.to_dict()}), 201

@guestbook_bp.route('/<int:entry_id>', methods=['PUT'])
def update_entry(entry_id):
    if not current_user.is_authenticated:
        return error_response('UNAUTHORIZED', '로그인이 필요합니다.', 401)
        
    entry = GuestbookEntry.query.get(entry_id)
    if not entry:
        return error_response('NOT_FOUND', '방명록을 찾을 수 없습니다.', 404)
        
    if entry.author_user_id != current_user.id:
        return error_response('FORBIDDEN', '수정 권한이 없습니다.', 403)
        
    data = request.get_json() or {}
    content = data.get('content')
    
    if not content or not content.strip():
        return error_response('VALIDATION_FAILED', '내용을 입력해주세요.', 400, {'content': 'Required'})
        
    entry.content = content.strip()
    db.session.commit()
    
    return jsonify({'status': 'success', 'data': entry.to_dict()})

@guestbook_bp.route('/<int:entry_id>', methods=['DELETE'])
def delete_entry(entry_id):
    if not current_user.is_authenticated:
        return error_response('UNAUTHORIZED', '로그인이 필요합니다.', 401)
        
    entry = GuestbookEntry.query.get(entry_id)
    if not entry:
        return error_response('NOT_FOUND', '방명록을 찾을 수 없습니다.', 404)
        
    if entry.author_user_id != current_user.id:
        return error_response('FORBIDDEN', '삭제 권한이 없습니다.', 403)
        
    db.session.delete(entry)
    db.session.commit()
    
    return jsonify({'status': 'success'})
