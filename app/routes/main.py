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


main_bp = Blueprint("main", __name__)


@main_bp.get("/")
def index():
    if current_user.is_authenticated:
        return redirect(url_for("main.frontend_page", page="main"))
    return render_template("index.html")


@main_bp.get("/<page>.html")
def frontend_page(page: str):
    """Serve the migrated Farmda screens from the Flask template folder."""
    allowed_pages = {
        "main",
        "diary",
        "dictionary",
        "plant-select",
        "dashboard",
        "dashboard-v2",
        "legacy-wireframe",
    }
    if page not in allowed_pages:
        return jsonify(status="error", message="page not found"), 404
    if page not in {"dictionary", "legacy-wireframe"} and not current_user.is_authenticated:
        return redirect(url_for("main.login", next=request.path))
    return render_template(f"{page}.html")


@main_bp.get("/css/<path:filename>")
def legacy_css(filename: str):
    """Keep the original static page paths working after the Flask migration."""
    return send_from_directory(main_bp.root_path + "/../static/css", filename)


@main_bp.get("/js/<path:filename>")
def legacy_js(filename: str):
    return send_from_directory(main_bp.root_path + "/../static/js", filename)


@main_bp.get("/login.html")
def login():
    if current_user.is_authenticated:
        return redirect(url_for("main.frontend_page", page="main"))
    return render_template("login.html")


@main_bp.get("/health")
def health():
    try:
        db.session.execute(text("SELECT 1"))
    except SQLAlchemyError:
        return jsonify(status="error", database="disconnected"), 503

    return jsonify(status="ok", database="connected")

