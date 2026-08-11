from flask import Blueprint, jsonify, request
from flask_login import current_user, login_required
from sqlalchemy.exc import IntegrityError

from ..extensions import db
from ..models import CareLog, Plant, PlantOwnership, PlantSpecies


plants_bp = Blueprint("plants", __name__, url_prefix="/api/v1/plants")

ACTION_TYPES = {"WATER", "SUNLIGHT", "PET", "IGNORE"}


def api_error(code: str, message: str, status: int, fields: dict | None = None):
    error = {"code": code, "message": message}
    if fields:
        error["fields"] = fields
    return jsonify(error=error), status


def _json_body():
    if not request.is_json:
        return None, api_error("JSON_REQUIRED", "JSON 형식의 요청이 필요합니다.", 415)
    body = request.get_json(silent=True)
    if not isinstance(body, dict):
        return None, api_error("INVALID_REQUEST", "요청 본문을 확인해 주세요.", 400)
    return body, None


def _owned_plant(plant_id: int):
    return (
        db.session.query(Plant, PlantOwnership)
        .join(PlantOwnership, PlantOwnership.plant_id == Plant.id)
        .filter(
            Plant.id == plant_id,
            PlantOwnership.owner_user_id == current_user.id,
            PlantOwnership.ended_at.is_(None),
        )
        .first()
    )


@plants_bp.get("")
@login_required
def list_plants():
    rows = (
        db.session.query(Plant, PlantOwnership)
        .join(PlantOwnership, PlantOwnership.plant_id == Plant.id)
        .filter(
            PlantOwnership.owner_user_id == current_user.id,
            PlantOwnership.ended_at.is_(None),
        )
        .order_by(PlantOwnership.started_at.desc(), Plant.id.desc())
        .all()
    )
    return jsonify(data={"plants": [plant.to_dict(owner) for plant, owner in rows]})


@plants_bp.post("")
@login_required
def create_plant():
    body, error = _json_body()
    if error:
        return error

    name = " ".join(str(body.get("name", "")).split()).strip()
    species_name = " ".join(
        str(body.get("speciesName", name)).split()
    ).strip()
    category = str(body.get("category", "")).strip() or None
    emoji = str(body.get("emoji", "")).strip() or None
    image_url = str(body.get("imageUrl", "")).strip() or None
    fields = {}
    if not 1 <= len(name) <= 50:
        fields["name"] = "식물 이름은 1자 이상 50자 이하로 입력해 주세요."
    if not 1 <= len(species_name) <= 50:
        fields["speciesName"] = "식물 종류 이름을 확인해 주세요."
    if category and len(category) > 30:
        fields["category"] = "식물 분류는 30자 이하로 입력해 주세요."
    if emoji and len(emoji) > 16:
        fields["emoji"] = "식물 이모지는 16자 이하로 입력해 주세요."
    if image_url and (
        len(image_url) > 2000
        or not image_url.startswith(("https://", "http://"))
    ):
        fields["imageUrl"] = "올바른 식물 이미지 주소가 필요합니다."
    if not image_url and not emoji:
        fields["plantVisual"] = "식물 이미지 또는 이모지가 필요합니다."
    if fields:
        return api_error("VALIDATION_ERROR", "입력값을 확인해 주세요.", 400, fields)

    species = PlantSpecies.query.filter_by(name=species_name).first()
    if not species:
        species = PlantSpecies(
            name=species_name,
            category=category,
            emoji=emoji,
            image_url=image_url,
        )
        db.session.add(species)
        db.session.flush()
    else:
        if category:
            species.category = category
        if emoji:
            species.emoji = emoji
        if image_url:
            species.image_url = image_url

    plant = Plant(
        species_id=species.id,
        name=name,
        growth_score=0,
        positive_energy=0,
        negative_energy=0,
        mood=None,
        status="GROWING",
    )
    db.session.add(plant)
    db.session.flush()
    ownership = PlantOwnership(
        plant_id=plant.id,
        owner_user_id=current_user.id,
        acquisition_type="ADOPTION",
    )
    db.session.add(ownership)
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return api_error("PLANT_CREATE_FAILED", "식물을 저장하지 못했습니다.", 409)

    return jsonify(data={"plant": plant.to_dict(ownership)}), 201


@plants_bp.get("/<int:plant_id>")
@login_required
def get_plant(plant_id: int):
    row = _owned_plant(plant_id)
    if not row:
        return api_error("PLANT_NOT_FOUND", "식물을 찾을 수 없습니다.", 404)
    plant, ownership = row
    return jsonify(data={"plant": plant.to_dict(ownership)})


@plants_bp.post("/<int:plant_id>/care")
@login_required
def care_for_plant(plant_id: int):
    body, error = _json_body()
    if error:
        return error

    action_type = str(body.get("actionType", "")).strip().upper()
    note = str(body.get("note", "")).strip() or None
    if action_type not in ACTION_TYPES:
        return api_error("INVALID_ACTION", "지원하지 않는 돌봄 동작입니다.", 400)
    if note and len(note) > 1000:
        return api_error("NOTE_TOO_LONG", "기록은 1000자 이하로 입력해 주세요.", 400)

    row = _owned_plant(plant_id)
    if not row:
        return api_error("PLANT_NOT_FOUND", "식물을 찾을 수 없습니다.", 404)
    plant, ownership = row
    if plant.growth_score >= 100:
        return api_error("PLANT_ALREADY_COMPLETE", "이미 성장을 완료한 식물입니다.", 409)

    previous_score = plant.growth_score
    is_negative = action_type == "IGNORE"
    positive_delta = 0 if is_negative else 5
    negative_delta = 5 if is_negative else 0
    plant.growth_score = min(100, plant.growth_score + 5)
    plant.positive_energy += positive_delta
    plant.negative_energy += negative_delta
    if plant.growth_score >= 100:
        plant.status = "GIFT_READY"

    db.session.add(
        CareLog(
            plant_id=plant.id,
            user_id=current_user.id,
            action_type=action_type,
            growth_delta=plant.growth_score - previous_score,
            positive_delta=positive_delta,
            negative_delta=negative_delta,
            note=note,
        )
    )
    db.session.commit()
    return jsonify(data={"plant": plant.to_dict(ownership)})
