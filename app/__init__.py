from flask import Flask

from .config import Config
from .extensions import db


def create_app() -> Flask:
    app = Flask(__name__, static_url_path="")
    app.config.from_object(Config)

    db.init_app(app)

    from .routes import main_bp

    app.register_blueprint(main_bp)
    return app

