from flask import Flask
from sqlalchemy.exc import SQLAlchemyError
from werkzeug.middleware.proxy_fix import ProxyFix

from .config import Config
from .extensions import db, login_manager, migrate, oauth
from .security import init_csrf


def _validate_production_config(app: Flask) -> None:
    if app.testing or app.config.get("APP_ENV") != "production":
        return

    secret_key = str(app.config.get("SECRET_KEY") or "")
    errors = []
    if len(secret_key) < 32 or secret_key in {
        "development-secret-key",
        "change-this-in-local-development",
    }:
        errors.append("SECRET_KEY must be a random value of at least 32 characters")
    if not app.config.get("SESSION_COOKIE_SECURE"):
        errors.append("SESSION_COOKIE_SECURE must be enabled")
    if not app.config.get("TRUST_PROXY"):
        errors.append("TRUST_PROXY must be enabled behind the production proxy")

    if errors:
        raise RuntimeError("Invalid production configuration: " + "; ".join(errors))


def create_app(config_overrides: dict | None = None) -> Flask:
    app = Flask(__name__, static_url_path="")
    app.config.from_object(Config)
    if config_overrides:
        app.config.update(config_overrides)

    _validate_production_config(app)

    if app.config.get("TRUST_PROXY"):
        app.wsgi_app = ProxyFix(
            app.wsgi_app,
            x_for=1,
            x_proto=1,
            x_host=1,
            x_port=1,
        )

    db.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)
    oauth.init_app(app)
    init_csrf(app)

    from .models import User
    from .routes import auth_bp, diary_bp, gifts_bp, main_bp, plants_bp
    from .routes.guestbook import guestbook_bp
    from .routes.chat import chat_bp

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
        from flask import current_app, jsonify, request

        db.session.rollback()
        current_app.logger.exception("Database request failed", exc_info=error)
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

    @app.after_request
    def add_security_headers(response):
        from flask import request

        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "SAMEORIGIN")
        response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
        response.headers.setdefault(
            "Permissions-Policy",
            "camera=(), microphone=(), geolocation=()",
        )
        if request.is_secure:
            response.headers.setdefault(
                "Strict-Transport-Security",
                "max-age=31536000",
            )
        if request.path.startswith("/api/"):
            response.headers.setdefault("Cache-Control", "no-store")
        return response

    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(chat_bp)
    app.register_blueprint(plants_bp)
    app.register_blueprint(gifts_bp)
    app.register_blueprint(diary_bp)
    app.register_blueprint(guestbook_bp)
    return app




