from flask import Blueprint, jsonify, render_template
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from ..extensions import db


main_bp = Blueprint("main", __name__)


@main_bp.get("/")
def index():
    return render_template("index.html")


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

