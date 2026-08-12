from __future__ import annotations

import secrets

from ..extensions import db
from ..models import Plant, PlantEpithetFragment


EPITHET_FRAGMENTS = {
    ("FIRST", "POSITIVE"): (
        "찬란한",
        "축복받은",
        "싱그러운",
        "다정한",
        "눈부신",
        "용감한",
        "포근한",
        "꿈꾸는",
        "생명력 넘치는",
        "햇살을 머금은",
        "별빛에 물든",
        "기적을 품은",
    ),
    ("SECOND", "POSITIVE"): (
        "새벽의",
        "햇살의",
        "별빛의",
        "봄바람의",
        "푸른 숲의",
        "생명의",
        "행운의",
        "희망의",
        "달빛의",
        "이슬의",
        "정원의",
        "무지개의",
    ),
    ("FIRST", "NEGATIVE"): (
        "뒤틀린",
        "저주받은",
        "타락한",
        "메마른",
        "잠식된",
        "폭주하는",
        "음산한",
        "잊혀진",
        "분노한",
        "광기에 젖은",
        "그림자에 물든",
        "종말을 부르는",
    ),
    ("SECOND", "NEGATIVE"): (
        "황천의",
        "심연의",
        "공허의",
        "망각의",
        "광기의",
        "파멸의",
        "어둠의",
        "폐허의",
        "독안개의",
        "붉은 달의",
        "균열의",
        "잿빛 밤의",
    ),
}


def energy_polarity(positive_energy: int, negative_energy: int) -> str:
    positive = int(positive_energy or 0)
    negative = int(negative_energy or 0)
    return "NEGATIVE" if negative > positive else "POSITIVE"


def ensure_epithet_fragments() -> None:
    existing = {
        (fragment.slot, fragment.polarity, fragment.text)
        for fragment in PlantEpithetFragment.query.all()
    }
    missing = [
        PlantEpithetFragment(slot=slot, polarity=polarity, text=text)
        for (slot, polarity), texts in EPITHET_FRAGMENTS.items()
        for text in texts
        if (slot, polarity, text) not in existing
    ]
    if missing:
        db.session.add_all(missing)
        db.session.flush()


def assign_plant_epithet(plant: Plant) -> None:
    ensure_epithet_fragments()
    polarity = energy_polarity(plant.positive_energy, plant.negative_energy)
    first_fragments = PlantEpithetFragment.query.filter_by(
        slot="FIRST", polarity=polarity, is_active=True
    ).all()
    second_fragments = PlantEpithetFragment.query.filter_by(
        slot="SECOND", polarity=polarity, is_active=True
    ).all()
    combinations = [
        (first, second)
        for first in first_fragments
        for second in second_fragments
        if (first.id, second.id)
        != (plant.epithet_first_id, plant.epithet_second_id)
    ]
    if not combinations:
        combinations = [
            (first, second)
            for first in first_fragments
            for second in second_fragments
        ]
    if not combinations:
        raise RuntimeError(f"{polarity} 수식어 조각이 부족합니다.")
    plant.epithet_first, plant.epithet_second = secrets.choice(combinations)


def refresh_epithet_after_state_change(
    plant: Plant,
    *,
    previous_stage: str,
    previous_polarity: str,
) -> bool:
    current_polarity = energy_polarity(
        plant.positive_energy,
        plant.negative_energy,
    )
    if plant.growth_stage == previous_stage and current_polarity == previous_polarity:
        return False
    assign_plant_epithet(plant)
    return True
