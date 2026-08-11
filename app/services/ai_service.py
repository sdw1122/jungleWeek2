import json
import os

from google import genai
from google.genai import types


POSITIVE_WORDS = ("사랑", "예뻐", "좋아", "고마워", "잘했어", "힘내", "행복", "멋져", "소중")
NEGATIVE_WORDS = ("싫어", "미워", "못생겼", "바보", "짜증", "죽어", "별로", "안 예뻐")


def local_response(user_message: str) -> dict:
    is_negative = any(word in user_message for word in NEGATIVE_WORDS)
    is_positive = any(word in user_message for word in POSITIVE_WORDS)
    if is_negative and not is_positive:
        return {
            "sentiment": "NEGATIVE",
            "response": "조금 속상해요. 그래도 곁에서 따뜻하게 지켜봐 주세요. 🌧️",
            "emotion": "속상",
            "positive_delta": 0,
            "negative_delta": 1,
        }
    return {
        "sentiment": "POSITIVE",
        "response": "말을 걸어줘서 고마워요! 마음과 잎이 함께 자라는 기분이에요. 🌱",
        "emotion": "기쁨",
        "positive_delta": 1,
        "negative_delta": 0,
    }


def analyze_chat(
    user_message: str,
    history: list | None = None,
    pos_energy: int = 0,
    neg_energy: int = 0,
) -> dict:
    api_key = os.getenv("GEMINI_API_KEY", "").strip()
    if not api_key:
        return local_response(user_message)

    try:
        positive_energy = int(pos_energy)
        negative_energy = int(neg_energy)
    except (TypeError, ValueError):
        positive_energy = 0
        negative_energy = 0

    if negative_energy > positive_energy:
        personality = (
            "관심이 부족해 서운하고 퉁명스러운 반려식물이다. "
            "무례하거나 공격적인 표현은 피하면서 짧고 솔직하게 답한다."
        )
    else:
        personality = (
            "밝고 긍정적인 귀여운 반려식물이다. 햇살, 잎사귀, 물, 뿌리처럼 "
            "식물다운 표현을 자연스럽게 사용하며 다정하게 답한다."
        )

    recent_history = "\n".join(
        f"- {'사용자' if item.get('role') == 'USER' else '식물'}: {item.get('content', '')}"
        for item in (history or [])[-10:]
    )
    prompt = f"""
역할: {personality}

최근 대화:
{recent_history or '- 이전 대화 없음'}

새 사용자 메시지: {user_message}

메시지가 식물에게 긍정적이면 POSITIVE, 부정적이면 NEGATIVE, 어느 쪽도 아니면 NEUTRAL로 분류한다.
감정은 한국어 2~6글자로, 답변은 한국어 두 문장 이내로 작성한다.
다음 JSON 형식만 반환한다:
{{"sentiment":"POSITIVE|NEGATIVE|NEUTRAL","emotion":"감정","response":"답변"}}
"""

    client = genai.Client(
        api_key=api_key,
        http_options=types.HttpOptions(timeout=15_000),
    )
    try:
        for model_name in ("gemini-2.5-flash", "gemini-2.0-flash"):
            try:
                response = client.models.generate_content(
                    model=model_name,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        response_mime_type="application/json"
                    ),
                )
                data = json.loads(response.text)
                sentiment = str(data.get("sentiment", "NEUTRAL")).upper()
                if sentiment not in {"POSITIVE", "NEGATIVE", "NEUTRAL"}:
                    sentiment = "NEUTRAL"
                return {
                    "sentiment": sentiment,
                    "response": str(
                        data.get("response") or "잠시 후 다시 말해 주세요."
                    ),
                    "emotion": str(data.get("emotion") or "평온"),
                    "positive_delta": 1 if sentiment == "POSITIVE" else 0,
                    "negative_delta": 1 if sentiment == "NEGATIVE" else 0,
                }
            except Exception:
                continue
    finally:
        client.close()

    return local_response(user_message)
