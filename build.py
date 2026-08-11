import os

def write_file(path, content):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)

# 1. Update models
write_file('app/models/plant.py', '''from __future__ import annotations
from datetime import datetime
from sqlalchemy import func
from ..extensions import db

class Plant(db.Model):
    __tablename__ = "plants"

    id = db.Column(db.BigInteger, primary_key=True)
    species_id = db.Column(db.BigInteger, nullable=False)
    name = db.Column(db.String(50), nullable=False)
    growth_score = db.Column(db.SmallInteger, nullable=False, default=0)
    positive_energy = db.Column(db.Integer, nullable=False, default=0)
    negative_energy = db.Column(db.Integer, nullable=False, default=0)
    status = db.Column(db.String(20), nullable=False, default="GROWING")
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = db.Column(db.DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())
''')

write_file('app/models/chat.py', '''from __future__ import annotations
from datetime import datetime
from sqlalchemy import func
from ..extensions import db

class ChatSession(db.Model):
    __tablename__ = "chat_sessions"

    id = db.Column(db.BigInteger, primary_key=True)
    plant_id = db.Column(db.BigInteger, db.ForeignKey("plants.id", ondelete="RESTRICT"), nullable=False)
    user_id = db.Column(db.BigInteger, db.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    started_at = db.Column(db.DateTime(timezone=True), nullable=False, server_default=func.now())
    ended_at = db.Column(db.DateTime(timezone=True))

class ChatMessage(db.Model):
    __tablename__ = "chat_messages"

    id = db.Column(db.BigInteger, primary_key=True)
    session_id = db.Column(db.BigInteger, db.ForeignKey("chat_sessions.id", ondelete="CASCADE"), nullable=False)
    role = db.Column(db.String(20), nullable=False)
    content = db.Column(db.Text, nullable=False)
    positive_delta = db.Column(db.Integer, nullable=False, default=0)
    negative_delta = db.Column(db.Integer, nullable=False, default=0)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, server_default=func.now())
''')

# Update models __init__.py
with open('app/models/__init__.py', 'r', encoding='utf-8') as f:
    models_init = f.read()
if 'Plant' not in models_init:
    models_init = models_init.replace('from .user import User', 'from .user import User\nfrom .plant import Plant\nfrom .chat import ChatSession, ChatMessage')
    models_init = models_init.replace('__all__ = ["User"]', '__all__ = ["User", "Plant", "ChatSession", "ChatMessage"]')
    write_file('app/models/__init__.py', models_init)

# 2. AI Service
write_file('app/services/ai_service.py', '''import os
import google.generativeai as genai
import json

def analyze_chat(user_message: str):
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return {"sentiment": "POSITIVE", "response": "API 키가 설정되지 않았습니다. 기본 긍정 메시지입니다.", "positive_delta": 1, "negative_delta": 0}
        
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-2.5-flash')
    
    prompt = f"""
    You are an AI for a virtual plant. The user said: "{user_message}"
    Analyze if the message is 'POSITIVE' or 'NEGATIVE' in sentiment.
    Then provide a short response as the plant.
    Respond in JSON format exactly like this:
    {{
        "sentiment": "POSITIVE" or "NEGATIVE",
        "response": "Your response here"
    }}
    """
    
    try:
        response = model.generate_content(prompt)
        text = response.text
        if "`json" in text:
            text = text.split("`json")[1].split("`")[0].strip()
        elif "`" in text:
            text = text.split("`")[1].strip()
            
        data = json.loads(text)
        sentiment = data.get("sentiment", "POSITIVE")
        reply = data.get("response", "고마워요!")
        
        pos_delta = 1 if sentiment == "POSITIVE" else 0
        neg_delta = 1 if sentiment == "NEGATIVE" else 0
        
        return {
            "sentiment": sentiment,
            "response": reply,
            "positive_delta": pos_delta,
            "negative_delta": neg_delta
        }
    except Exception as e:
        print("AI Error:", e)
        return {"sentiment": "POSITIVE", "response": "앗, 잘 못 들었어요! 긍정적으로 생각할게요.", "positive_delta": 1, "negative_delta": 0}
''')

# 3. Chat Route
write_file('app/routes/chat.py', '''from flask import Blueprint, request, jsonify
from ..extensions import db
from ..models.plant import Plant
from ..models.chat import ChatSession, ChatMessage
from ..services.ai_service import analyze_chat
from flask_login import current_user, login_required

chat_bp = Blueprint('chat', __name__, url_prefix='/api/chat')

@chat_bp.route('/', methods=['POST'])
@login_required
def chat():
    data = request.get_json()
    message = data.get("message")
    plant_id = data.get("plant_id")
    
    if not message or not plant_id:
        return jsonify({"error": "message and plant_id are required"}), 400
        
    plant = Plant.query.get(plant_id)
    if not plant:
        return jsonify({"error": "Plant not found"}), 404
        
    session = ChatSession.query.filter_by(plant_id=plant_id, user_id=current_user.id, ended_at=None).first()
    if not session:
        session = ChatSession(plant_id=plant_id, user_id=current_user.id)
        db.session.add(session)
        db.session.commit()
        
    user_msg = ChatMessage(session_id=session.id, role="USER", content=message)
    db.session.add(user_msg)
    
    ai_result = analyze_chat(message)
    
    plant_msg = ChatMessage(
        session_id=session.id, 
        role="PLANT", 
        content=ai_result["response"],
        positive_delta=ai_result["positive_delta"],
        negative_delta=ai_result["negative_delta"]
    )
    db.session.add(plant_msg)
    
    if ai_result["sentiment"] == "POSITIVE":
        plant.positive_energy += 1
    else:
        plant.negative_energy += 1
        
    db.session.commit()
    
    return jsonify({
        "response": ai_result["response"],
        "sentiment": ai_result["sentiment"],
        "positive_energy": plant.positive_energy,
        "negative_energy": plant.negative_energy,
        "total_energy": plant.positive_energy + plant.negative_energy
    })
''')

# Update app/__init__.py to register blueprint
init_file = 'app/__init__.py'
if os.path.exists(init_file):
    with open(init_file, 'r', encoding='utf-8') as f:
        app_init = f.read()
    if 'chat_bp' not in app_init:
        # Extremely basic injection - just finding a place after other blueprints
        if 'from .routes.main import main_bp' in app_init:
            app_init = app_init.replace('from .routes.main import main_bp', 'from .routes.main import main_bp\\n    from .routes.chat import chat_bp')
            app_init = app_init.replace('app.register_blueprint(main_bp)', 'app.register_blueprint(main_bp)\\n    app.register_blueprint(chat_bp)')
        else:
            app_init += '\\nfrom .routes.chat import chat_bp\\napp.register_blueprint(chat_bp)\\n'
        write_file(init_file, app_init)

# Add google-generativeai to requirements
with open('requirements.txt', 'a', encoding='utf-8') as f:
    f.write('\\ngoogle-generativeai\\n')

print("Code generated successfully!")
