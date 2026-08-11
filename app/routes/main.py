from flask import Blueprint, jsonify, render_template, send_from_directory
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from ..extensions import db


main_bp = Blueprint("main", __name__)


@main_bp.get("/")
def index():
    return render_template("index.html")


@main_bp.get("/<page>.html")
def frontend_page(page: str):
    """Serve the migrated Farmda screens from the Flask template folder."""
    allowed_pages = {
        "main",
        "diary",
        "plant-select",
        "dashboard",
        "dashboard-v2",
        "legacy-wireframe",
    }
    if page not in allowed_pages:
        return jsonify(status="error", message="page not found"), 404
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
    return render_template("login.html")


@main_bp.get("/main.html")
def main_page():
    return render_template("main.html")


@main_bp.get("/dictionary.html")
def dictionary():
    return render_template("dictionary.html")


@main_bp.get("/plant-select.html")
def plant_select():
    return render_template("plant-select.html")


@main_bp.get("/dashboard.html")
def dashboard():
    return render_template("dashboard.html")


@main_bp.get("/dashboard-v2.html")
def dashboard_v2():
    return render_template("dashboard-v2.html")


@main_bp.get("/health")
def health():
    try:
        db.session.execute(text("SELECT 1"))
    except SQLAlchemyError:
        return jsonify(status="error", database="disconnected"), 503

    return jsonify(status="ok", database="connected")

