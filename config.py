import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-key-change-in-production")
    SQLALCHEMY_DATABASE_URI = "sqlite:///" + os.path.join(BASE_DIR, "v1fresh.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Business rules
    FREE_DELIVERY_THRESHOLD = 299      # ₹ — orders above this ship free
    DELIVERY_FEE = 25                  # ₹ — flat fee below threshold
    CURRENCY_SYMBOL = "₹"
