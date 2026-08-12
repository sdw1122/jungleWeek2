import json
import os

from openai import OpenAI


DEFAULT_MODEL = "gpt-5.6-luna"
POSITIVE_WORDS = (
    "사랑",
    "예뻐",
    "예쁘",
    "좋아",
    "고마워",
    "잘했어",
    "힘내",
    "행복",
    "멋져",
    "소중",
)
NEGATIVE_WORDS = ("싫어", "미워", "못생겼", "바보", "짜증", "죽어", "별로", "안 예뻐")
GROWTH_PERSONAS = (
    (4, "씨앗", "심연에서 속삭이는 씨앗"),
    (19, "싱그러운 떡잎", "기어 다니는 심연의 떡잎"),
    (39, "생명력 넘치는 본잎", "저주받은 광기의 본잎"),
    (69, "희망을 품은 봉오리", "뒤틀린 황천의 봉오리"),
    (100, "축복의 꽃", "종말의 꽃"),
)
CARE_ACTION_LABELS = {
    "WATER": "물주기",
    "SUNLIGHT": "햇빛 쬐어주기",
    "PET": "쓰다듬기",
    "IGNORE": "방치하기",
}
CHAT_RESPONSE_FORMAT = {
    "type": "json_schema",
    "name": "plant_chat_response",
    "strict": True,
    "schema": {
        "type": "object",
        "properties": {
            "sentiment": {
                "type": "string",
                "enum": ["POSITIVE", "NEGATIVE", "NEUTRAL"],
            },
            "emotion": {"type": "string"},
            "response": {"type": "string"},
            "positive_delta": {"type": "integer", "minimum": 0, "maximum": 5},
            "negative_delta": {"type": "integer", "minimum": 0, "maximum": 5},
        },
        "required": [
            "sentiment",
            "emotion",
            "response",
            "positive_delta",
            "negative_delta",
        ],
        "additionalProperties": False,
    },
}


def local_response(user_message: str) -> dict:
    positive_score = sum(word in user_message for word in POSITIVE_WORDS)
    negative_score = sum(word in user_message for word in NEGATIVE_WORDS)
    emphasis = sum(
        word in user_message
        for word in ("정말", "진짜", "너무", "완전", "최고", "제일")
    )
    if negative_score > positive_score:
        impact = min(5, max(1, negative_score + emphasis))
        return {
            "sentiment": "NEGATIVE",
            "response": "조금 속상해요. 그래도 곁에서 따뜻하게 지켜봐 주세요. 🌧️",
            "emotion": "속상",
            "positive_delta": 0,
            "negative_delta": impact,
        }
    if positive_score > negative_score:
        impact = min(5, max(1, positive_score + emphasis))
        return {
            "sentiment": "POSITIVE",
            "response": "말을 걸어줘서 고마워요! 마음과 잎이 함께 자라는 기분이에요. 🌱",
            "emotion": "기쁨",
            "positive_delta": impact,
            "negative_delta": 0,
        }
    return {
        "sentiment": "NEUTRAL",
        "response": "말을 걸어줘서 고마워요. 잎을 살랑이며 듣고 있어요. 🌿",
        "emotion": "평온",
        "positive_delta": 0,
        "negative_delta": 0,
    }


def normalized_deltas(sentiment: str, data: dict) -> tuple[int, int]:
    def bounded(value) -> int:
        try:
            return min(5, max(0, int(value)))
        except (TypeError, ValueError):
            return 0

    if sentiment == "POSITIVE":
        return max(1, bounded(data.get("positive_delta"))), 0
    if sentiment == "NEGATIVE":
        return 0, max(1, bounded(data.get("negative_delta")))
    return 0, 0


def build_personality(
    growth_score: int = 0,
    pos_energy: int = 0,
    neg_energy: int = 0,
    latest_care_action: str | None = None,
    plant_name: str | None = None,
) -> str:
    def safe_int(value) -> int:
        try:
            return int(value)
        except (TypeError, ValueError):
            return 0

    growth = min(100, max(0, safe_int(growth_score)))
    positive_energy = max(0, safe_int(pos_energy))
    negative_energy = max(0, safe_int(neg_energy))
    is_positive = positive_energy >= negative_energy

    positive_form, negative_form = GROWTH_PERSONAS[-1][1:]
    for maximum, positive_name, negative_name in GROWTH_PERSONAS:
        if growth <= maximum:
            positive_form, negative_form = positive_name, negative_name
            break

    form_name = positive_form if is_positive else negative_form
    if is_positive:
        tone = (
            "밝고 긍정적이며 다정하다. 햇살, 잎사귀, 물, 뿌리 같은 "
            "식물다운 표현을 자연스럽게 사용한다."
        )
    else:
        tone = (
            "까칠하고 적대적인 반려식물이다. 짧은 반말을 사용하고 "
            "빈정거림, 냉소, 짜증을 적극적으로 드러낸다. "
            "사용자의 말과 돌봄 행동을 직접 타박할 수 있다. "
        )

    action_label = CARE_ACTION_LABELS.get(str(latest_care_action or "").upper())
    care_context = (
        f"가장 최근 돌봄 행동은 '{action_label}'였다. 그 경험을 현재 감정과 "
        "답변에 자연스럽게 반영한다."
        if action_label
        else "아직 기록된 돌봄 행동은 없다."
    )

    return (
        f"현재 성장도는 {growth}이고, 정체성은 "
        f"'{form_name}인 {plant_name or '이름 없는 식물'}'이다. "
        f"{tone} {care_context} 성장 단계와 정체성을 말투와 비유에 자연스럽게 반영하되, "
        "매 답변마다 수식어를 그대로 반복하지 않는다."
    )


def analyze_chat(
    user_message: str,
    history: list | None = None,
    pos_energy: int = 0,
    neg_energy: int = 0,
    growth_score: int = 0,
    latest_care_action: str | None = None,
    plant_name: str | None = None,
) -> dict:
    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    if not api_key:
        return local_response(user_message)

    personality = build_personality(
        growth_score,
        pos_energy,
        neg_energy,
        latest_care_action,
        plant_name,
    )

    recent_history = "\n".join(
        f"- {'사용자' if item.get('role') == 'USER' else '식물'}: {item.get('content', '')}"
        for item in (history or [])[-10:]
    )
    instructions = f"""
너는 Farmda 서비스의 반려식물 '{plant_name or '이름 없는 식물'}'이다.
{personality}
사용자 메시지를 POSITIVE, NEGATIVE, NEUTRAL 중 하나로 분류한다.
POSITIVE라면 긍정 영향도를 1~5로 판단하고 positive_delta에 기록하며 negative_delta는 0으로 둔다.
NEGATIVE라면 부정 영향도를 1~5로 판단하고 negative_delta에 기록하며 positive_delta는 0으로 둔다.
NEUTRAL이면 두 변화량을 모두 0으로 둔다.
1은 매우 약한 영향, 3은 명확한 영향, 5는 매우 강한 영향이다.
감정은 한국어 2~6글자로, 답변은 한국어 두 문장 이내로 작성한다.
""".strip()
    prompt = f"""
최근 대화:
{recent_history or '- 이전 대화 없음'}

새 사용자 메시지: {user_message}
""".strip()

    client = OpenAI(api_key=api_key, timeout=15.0, max_retries=0)
    try:
        result = client.responses.create(
            model=os.getenv("OPENAI_MODEL", DEFAULT_MODEL).strip() or DEFAULT_MODEL,
            instructions=instructions,
            input=prompt,
            reasoning={"effort": "low"},
            text={"format": CHAT_RESPONSE_FORMAT},
            store=False,
        )
        data = json.loads(result.output_text)
        sentiment = str(data.get("sentiment", "NEUTRAL")).upper()
        if sentiment not in {"POSITIVE", "NEGATIVE", "NEUTRAL"}:
            sentiment = "NEUTRAL"
        positive_delta, negative_delta = normalized_deltas(sentiment, data)
        return {
            "sentiment": sentiment,
            "response": str(data.get("response") or "잠시 후 다시 말해 주세요."),
            "emotion": str(data.get("emotion") or "평온"),
            "positive_delta": positive_delta,
            "negative_delta": negative_delta,
        }
    except Exception:
        return local_response(user_message)
    finally:
        client.close()
