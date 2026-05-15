import os
import logging
from flask import Flask, redirect, url_for, request

from .config import load_config
from .db import init_sqlite, close_sqlite


def create_app(config_overrides=None):
    app = Flask(
        __name__,
        template_folder="templates",
        static_folder="static",
    )

    cfg = load_config()
    app.config.update(cfg)
    if config_overrides:
        app.config.update(config_overrides)

    os.makedirs(app.config["UPLOAD_DIR"], exist_ok=True)
    os.makedirs(os.path.dirname(app.config["DATABASE_PATH"]) or ".", exist_ok=True)

    _configure_logging(app)

    app.teardown_appcontext(close_sqlite)

    with app.app_context():
        init_sqlite()

    from .api.routes import bp as api_bp
    from .auth.routes import bp as auth_bp
    from .auth.oauth import bp as oauth_bp
    from .auth.magic_link import bp as magic_link_bp
    from .slots.routes import bp as slots_bp
    from .admin.routes import bp as admin_bp
    from .admin.health import bp as admin_health_bp
    from .uploads.routes import bp as uploads_bp
    from .internal.routes import bp as internal_bp
    from .profile.routes import bp as profile_bp

    app.register_blueprint(api_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(oauth_bp)
    app.register_blueprint(magic_link_bp)
    app.register_blueprint(slots_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(admin_health_bp)
    app.register_blueprint(uploads_bp)
    app.register_blueprint(internal_bp)
    app.register_blueprint(profile_bp)

    @app.after_request
    def _api_cors(response):
        if request.path.startswith("/api/"):
            origin = request.headers.get("Origin")
            if origin:
                response.headers["Access-Control-Allow-Origin"] = origin
                response.headers["Access-Control-Allow-Credentials"] = "true"
                response.headers["Access-Control-Allow-Methods"] = (
                    "GET, POST, PATCH, PUT, DELETE, OPTIONS"
                )
                response.headers["Access-Control-Allow-Headers"] = (
                    "Content-Type, Authorization"
                )
        return response

    @app.route("/")
    def home():
        return redirect(url_for("auth.login"))

    return app


def _configure_logging(app):
    log_path = os.path.join(app.config["UPLOAD_DIR"], "logs3.txt")
    logging.basicConfig(
        level=logging.DEBUG if app.config.get("DEBUG") else logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler(log_path),
            logging.StreamHandler(),
        ],
    )
