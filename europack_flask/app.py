"""Application factory for the Europack Flask website."""
import os

from flask import Flask, render_template

from config import config_by_name
from models import db, init_db


def create_app(config_name=None):
    """Create and configure the Flask application instance.

    Args:
        config_name: One of "development", "production", "default".
            Falls back to the FLASK_ENV environment variable, then
            to "default".
    """
    if config_name is None:
        config_name = os.environ.get("FLASK_ENV", "default")

    app = Flask(__name__)
    app.config.from_object(config_by_name.get(config_name, config_by_name["default"]))

    init_db(app)

    from routes.main import main as main_blueprint
    app.register_blueprint(main_blueprint)

    register_error_handlers(app)

    # Dev convenience: create tables if they do not exist yet.
    with app.app_context():
        try:
            db.create_all()
        except Exception:  # noqa: BLE001
            pass

    return app


def register_error_handlers(app):
    """Attach custom 404 / 500 error pages to the app."""

    @app.errorhandler(404)
    def not_found(error):  # noqa: ANN001
        return render_template("errors/404.html"), 404

    @app.errorhandler(500)
    def server_error(error):  # noqa: ANN001
        return render_template("errors/500.html"), 500


app = create_app()

if __name__ == "__main__":
    app.run(debug=True)
