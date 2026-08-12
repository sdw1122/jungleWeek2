import json
import os

from openai import OpenAI

from .ai_service import DEFAULT_MODEL, build_personality


DIARY_RESPONSE_FORMAT = {
    "type": "json_schema",
    "name": "plant_diary_draft",
    "strict": True,
    "schema": {
        "type": "object",
        "properties": {
            "title": {"type": "string"},
            "content": {"type": "string"},
        },
        "required": ["title", "content"],
        "additionalProperties": False,
    },
}


ACTION_LABELS = {
    "WATER": "물을 마셨다",
    "SUNLIGHT": "햇빛을 쬐었다",
    "PET": "쓰다듬어 주었다",
    "IGNORE": "방치되었다",
}


def local_diary_draft(
    plant_name: str,
    mood: str | None,
    activity_summary: dict,
) -> dict:
    care_actions = activity_summary.get("careActions") or []
    chat = activity_summary.get("chat") or {}
    moments = []
    for action in care_actions:
        label = ACTION_LABELS.get(action.get("actionType"), "돌봄을 받았다")
        count = max(1, int(action.get("count", 1) or 1))
        moments.append(f"{label}{f'({count}번)' if count > 1 else ''}")
    if chat.get("messageCount"):
        moments.append("주인님과 이야기를 나눴다")

    if not moments:
        title = "조용히 기다린 하루"
        content = (
            "오늘은 특별한 돌봄이나 대화 없이 조용히 시간을 보냈다. "
            "내일은 주인님의 따뜻한 목소리와 손길을 만날 수 있으면 좋겠다."
        )
    else:
        title = f"{mood or '평온함'}을 느낀 성장의 하루"
        content = (
            f"오늘은 {', '.join(moments)}. "
            f"{plant_name}인 나는 그 마음을 기억하며 조금 더 단단해진 기분이다."
        )
    return {"title": title[:150], "content": content[:2000], "fallback": True}


def generate_diary_draft(
    *,
    plant_name: str,
    mood: str | None,
    growth_score: int,
    positive_energy: int,
    negative_energy: int,
    latest_care_action: str | None,
    activity_summary: dict,
    recent_messages: list[dict],
) -> dict:
    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    if not api_key:
        return local_diary_draft(plant_name, mood, activity_summary)

    personality = build_personality(
        growth_score,
        positive_energy,
        negative_energy,
        latest_care_action,
        plant_name,
    )
    activity_text = json.dumps(activity_summary, ensure_ascii=False)
    conversation = "\n".join(
        f"- {'주인' if item.get('role') == 'USER' else '식물'}: {item.get('content', '')}"
        for item in recent_messages[-20:]
    )
    instructions = f"""
너는 Farmda의 반려식물 '{plant_name}'이다.
{personality}
오늘 하루를 돌아보며 식물의 1인칭 관점으로 한국어 성장일기를 쓴다.
제목은 150자 이하, 본문은 2,000자 이하로 작성한다.
실제로 제공된 돌봄과 대화만 언급하고 존재하지 않는 사건을 만들지 않는다.
활동이 없다면 기다림과 현재 감정을 중심으로 조용한 하루를 기록한다.
공격적인 성격이어도 혐오·위협 표현은 사용하지 않는다.
""".strip()
    prompt = f"""
현재 기분: {mood or '기록 없음'}
오늘 활동 요약: {activity_text}
오늘 최근 대화:
{conversation or '- 대화 없음'}
""".strip()

    client = OpenAI(api_key=api_key, timeout=20.0, max_retries=0)
    try:
        result = client.responses.create(
            model=os.getenv("OPENAI_MODEL", DEFAULT_MODEL).strip() or DEFAULT_MODEL,
            instructions=instructions,
            input=prompt,
            reasoning={"effort": "low"},
            text={"format": DIARY_RESPONSE_FORMAT},
            store=False,
        )
        data = json.loads(result.output_text)
        title = " ".join(str(data.get("title", "")).split()).strip()
        content = str(data.get("content", "")).strip()
        if not title or not content:
            raise ValueError("Empty diary draft")
        return {"title": title[:150], "content": content[:2000], "fallback": False}
    except Exception:
        return local_diary_draft(plant_name, mood, activity_summary)
    finally:
        client.close()
