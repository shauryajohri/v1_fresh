"""Database extension setup for the Europack Flask application."""
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


def init_db(app):
    """Bind the SQLAlchemy instance to the given Flask app.

    Import models here so they are registered on the metadata before
    any db.create_all() call is issued.
    """
    db.init_app(app)
    with app.app_context():
        from models import models  # noqa: F401
