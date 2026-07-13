"""
Shared extension instances.
Kept in their own module so models.py and routes/*.py can both import
`db` without creating circular imports with app.py.
"""
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()
