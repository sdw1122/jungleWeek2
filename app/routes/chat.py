from flask import Blueprint, request, jsonify
from ..extensions import db
from ..models.plant import Plant
from ..models.chat import ChatSession, ChatMessage
from ..services.ai_service import analyze_chat
from flask_login import current_user, login_required

chat_bp = Blueprint('chat', __name__, url_prefix='/api/chat')

@chat_bp.route('', methods=['POST'])
@login_required
def chat():
    data = request.get_json()
    message = data.get('message')
    plant_id = data.get('plant_id')
    
    if not message or not plant_id:
        return jsonify({'error': 'message and plant_id are required'}), 400
        
    plant = Plant.query.get(plant_id)
    
    if not plant:
        ai_result = analyze_chat(message, [], 0, 0)
        return jsonify({
            'response': ai_result['response'],
            'sentiment': ai_result['sentiment'],
            'emotion': ai_result.get('emotion', '평온'),
            'positive_energy': ai_result['positive_delta'],
            'negative_energy': ai_result['negative_delta'],
            'total_energy': ai_result['positive_delta'] + ai_result['negative_delta']
        })
        
    session = ChatSession.query.filter_by(plant_id=plant_id, user_id=current_user.id, ended_at=None).first()
    if not session:
        session = ChatSession(plant_id=plant_id, user_id=current_user.id)
        db.session.add(session)
        db.session.commit()
        
    past_messages = ChatMessage.query.filter_by(session_id=session.id).order_by(ChatMessage.created_at.desc()).limit(10).all()
    past_messages.reverse()
    history = [{"role": m.role, "content": m.content} for m in past_messages]
    
    ai_result = analyze_chat(message, history, plant.positive_energy, plant.negative_energy)
    
    user_msg = ChatMessage(session_id=session.id, role='USER', content=message)
    db.session.add(user_msg)
    
    plant_msg = ChatMessage(
        session_id=session.id, 
        role='PLANT', 
        content=ai_result['response'],
        positive_delta=ai_result['positive_delta'],
        negative_delta=ai_result['negative_delta']
    )
    db.session.add(plant_msg)
    
    if ai_result['sentiment'] == 'POSITIVE':
        plant.positive_energy += 1
    elif ai_result['sentiment'] == 'NEGATIVE':
        plant.negative_energy += 1
        
    db.session.commit()
    
    return jsonify({
        'response': ai_result['response'],
        'sentiment': ai_result['sentiment'],
        'emotion': ai_result.get('emotion', '평온'),
        'positive_energy': plant.positive_energy,
        'negative_energy': plant.negative_energy,
        'total_energy': plant.positive_energy + plant.negative_energy
    })

