"""
One-off helper: insert (or update) a single admin login.
Run with: python add_admin.py
"""
from werkzeug.security import generate_password_hash
from app import create_app
from extensions import db
from models import Admin

USERNAME = "shaurya"
PASSWORD = "12345"

app = create_app()
with app.app_context():
    admin = Admin.query.filter_by(username=USERNAME).first()
    if admin:
        admin.password_hash = generate_password_hash(PASSWORD)
        print(f"Updated existing admin '{USERNAME}'.")
    else:
        admin = Admin(username=USERNAME, password_hash=generate_password_hash(PASSWORD))
        db.session.add(admin)
        print(f"Created new admin '{USERNAME}'.")
    db.session.commit()
    print("Done. Current admins:", [a.username for a in Admin.query.all()])
