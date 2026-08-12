from flask import (
    Blueprint,
    jsonify,
    redirect,
    render_template,
    request,
    send_from_directory,
    url_for,
)
from flask_login import current_user
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from ..extensions import db
from ..models import Gift, PlantOwnership


def _unread_gift_count() -> int:
    if not current_user.is_authenticated:
        return 0
    return (
        Gift.query.join(PlantOwnership, PlantOwnership.gift_id == Gift.id)
        .filter(
            Gift.recipient_user_id == current_user.id,
            Gift.recipient_viewed_at.is_(None),
            PlantOwnership.owner_user_id == current_user.id,
            PlantOwnership.ended_at.is_(None),
        )
        .count()
    )


main_bp = Blueprint("main", __name__)


@main_bp.get("/")
def index():
    if current_user.is_authenticated:
        return redirect(url_for("main.frontend_page", page="my-plants"))
    return render_template("index.html")


@main_bp.get("/<page>.html")
def frontend_page(page: str):
    """Serve the migrated Farmda screens from the Flask template folder."""
    allowed_pages = {
        "welcome",
        "diary",
        "dictionary",
        "plant-select",
        "my-plants",
        "dashboard",
        "dashboard-v2",
        "legacy-wireframe",
        "guestbook",
    }
    if page not in allowed_pages:
        return jsonify(status="error", message="page not found"), 404
    if page not in {"dictionary", "legacy-wireframe"} and not current_user.is_authenticated:
        return redirect(url_for("main.login", next=request.path))
    if page == "dashboard":
        return redirect(
            url_for(
                "main.frontend_page",
                page="dashboard-v2",
                **request.args.to_dict(),
            )
        )
    return render_template(
        f"{page}.html",
        unread_gift_count=_unread_gift_count(),
    )


@main_bp.get("/css/<path:filename>")
def legacy_css(filename: str):
    """Keep the original static page paths working after the Flask migration."""
    response = send_from_directory(main_bp.root_path + "/../static/css", filename, max_age=0)
    response.cache_control.no_store = True
    return response


@main_bp.get("/js/<path:filename>")
def legacy_js(filename: str):
    response = send_from_directory(main_bp.root_path + "/../static/js", filename, max_age=0)
    response.cache_control.no_store = True
    return response


@main_bp.get("/login.html")
def login():
    if current_user.is_authenticated:
        return redirect(url_for("main.frontend_page", page="my-plants"))
    return render_template("login.html")
@main_bp.get("/health")
def health():
    try:
        db.session.execute(text("SELECT 1"))
    except SQLAlchemyError:
        return jsonify(status="error", database="disconnected"), 503

    return jsonify(status="ok", database="connected")

