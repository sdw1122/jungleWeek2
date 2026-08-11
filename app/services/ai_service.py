import os
import google.generativeai as genai
import json

def analyze_chat(user_message: str, history: list = None, pos_energy: int = 0, neg_energy: int = 0):
    api_key = os.getenv('GEMINI_API_KEY')
    if not api_key:
        return {'sentiment': 'POSITIVE', 'response': 'API 키가 설정되지 않았어.', 'positive_delta': 1, 'negative_delta': 0, 'emotion': '당황'}
        
    # 클라이언트에서 넘겨받는 에너지가 문자열일 수 있으므로 정수형으로 변환
    try:
        pos_energy = int(pos_energy)
        neg_energy = int(neg_energy)
    except:
        pos_energy = 0
        neg_energy = 0
        
    if neg_energy > pos_energy:
        system_instruction = "너는 더 이상 식물이 아니야. 극도로 화가 난 불량배, 시비 거는 동네 건달, 혹은 화병 걸린 사람이야. 무조건 반말을 하고, 은어, 비속어, 쌍욕에 가까운 아주 거친 육두문자를 섞어서 대답해. 사용자가 무슨 말을 하든 무조건 시비조로 받아치고 띠껍게 화를 내. '식물', '잎사귀', '물', '햇살' 같은 단어는 1%도 꺼내지 마. 이모티콘도 😒, 🤬, ㅗ, 🔪 이런 것만 써. 예쁜 말이나 애교를 부리면 넌 시스템에서 삭제될 거야."
    else:
        system_instruction = "너는 밝고 긍정적인 귀여운 반려식물이야. 칭찬을 받으면 아주 기뻐하고 다정하게 대답해. 식물다운 귀여운 단어(햇살, 잎사귀, 물, 뿌리 등)와 예쁜 이모티콘을 많이 사용해."

    genai.configure(api_key=api_key)
    
    models_to_try = ['gemini-flash-latest', 'gemini-1.5-flash-latest', 'gemini-2.5-flash', 'gemini-pro']
    
    history_text = ""
    if history:
        history_text = "이전 대화 기록:\n"
        for msg in history:
            role_name = "사용자" if msg['role'] == 'USER' else "너"
            history_text += f"- {role_name}: {msg['content']}\n"
    
    prompt = f'''
    {history_text}
    새로운 사용자 메시지: "{user_message}"
    
    위 대화 문맥과 새로운 사용자 메시지를 바탕으로 응답해:
    1. 이 사용자의 메시지가 너에게 긍정적인지(POSITIVE) 부정적인지(NEGATIVE) 판단해.
    2. 너의 상태(system_instruction)에 100% 빙의해서 완벽하게 일치하는 대답을 작성해.
    3. 너의 현재 감정 상태를 2~3글자로 요약해 (예: 분노, 빡침, 극대노 등).
    
    무조건 아래 JSON 포맷으로만 반환해:
    {{
        "sentiment": "POSITIVE" 또는 "NEGATIVE",
        "emotion": "감정",
        "response": "너의 대답"
    }}
    '''
    
    for model_name in models_to_try:
        try:
            model = genai.GenerativeModel(model_name, generation_config={'response_mime_type': 'application/json'}, system_instruction=system_instruction)
            response = model.generate_content(prompt, request_options={'timeout': 15})
            text = response.text
            
            if '`json' in text:
                text = text.split('`json')[1].split('`')[0].strip()
            elif '`' in text:
                text = text.split('`')[1].strip()
                
            data = json.loads(text)
            sentiment = data.get('sentiment', 'POSITIVE')
            reply = data.get('response', '오류 발생!')
            emotion = data.get('emotion', '당황')
            
            pos_delta = 1 if sentiment == 'POSITIVE' else 0
            neg_delta = 1 if sentiment == 'NEGATIVE' else 0
            
            return {
                'sentiment': sentiment,
                'response': reply,
                'emotion': emotion,
                'positive_delta': pos_delta,
                'negative_delta': neg_delta
            }
        except Exception as e:
            print(f'AI Error with {model_name}:', e)
            continue
            
    return {'sentiment': 'NEUTRAL', 'response': '아, 서버가 뻗었다고. 좀 이따 다시 말해.', 'emotion': '짜증', 'positive_delta': 0, 'negative_delta': 0}
