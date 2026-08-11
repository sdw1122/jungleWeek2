from flask import Flask
from sqlalchemy.exc import SQLAlchemyError

from .config import Config
from .extensions import db, login_manager, migrate, oauth
from .security import init_csrf


def create_app(config_overrides: dict | None = None) -> Flask:
    app = Flask(__name__, static_url_path="")
    app.config.from_object(Config)
    if config_overrides:
        app.config.update(config_overrides)

    db.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)
    oauth.init_app(app)
    init_csrf(app)

    from .models import User
    from .routes import auth_bp, main_bp, plants_bp

    @login_manager.user_loader
    def load_user(user_id: str):
        try:
            user = db.session.get(User, int(user_id))
        except (TypeError, ValueError):
            return None
        return user if user and user.is_active else None

    @login_manager.unauthorized_handler
    def unauthorized():
        from flask import jsonify, redirect, request, url_for

        if request.path.startswith("/api/"):
            return (
                jsonify(
                    error={
                        "code": "AUTHENTICATION_REQUIRED",
                        "message": "로그인이 필요합니다.",
                    }
                ),
                401,
            )
        return redirect(url_for("main.login", next=request.path))

    @app.errorhandler(SQLAlchemyError)
    def handle_database_error(error):
        from flask import jsonify, request

        db.session.rollback()
        if request.path.startswith("/api/"):
            return (
                jsonify(
                    error={
                        "code": "DATABASE_UNAVAILABLE",
                        "message": "데이터베이스에 연결할 수 없습니다.",
                    }
                ),
                503,
            )
        raise error

    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(plants_bp)
    return app

