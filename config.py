import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

# Load keys from a local .env file if present, so GOOGLE_CLIENT_ID / SECRET etc.
# can live in one file instead of being typed into the terminal each time.
# Safe no-op if python-dotenv isn't installed.
try:
    from dotenv import load_dotenv
    load_dotenv(os.path.join(BASE_DIR, ".env"))
except ImportError:
    pass


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-key-change-in-production")
    SQLALCHEMY_DATABASE_URI = "sqlite:///" + os.path.join(BASE_DIR, "v1fresh.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # If you deploy behind an HTTPS reverse proxy (Render, Railway, etc.), set
    # PREFERRED_URL_SCHEME=https as an env var so url_for(_external) and the
    # OAuth redirect URI match what Google expects. Defaults to http for local dev.
    PREFERRED_URL_SCHEME = os.environ.get("PREFERRED_URL_SCHEME", "http")

    # Google OAuth (set these as environment variables on your host / locally)
    GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID")
    GOOGLE_CLIENT_SECRET = os.environ.get("GOOGLE_CLIENT_SECRET")

    # Firebase phone-OTP (client-side). These values are meant to be public
    # (they ship to the browser), so they're safe to expose in the page.
    # If FIREBASE_API_KEY is empty, the phone tab falls back to on-screen demo OTP.
    FIREBASE_API_KEY = os.environ.get("FIREBASE_API_KEY")
    FIREBASE_AUTH_DOMAIN = os.environ.get("FIREBASE_AUTH_DOMAIN")
    FIREBASE_PROJECT_ID = os.environ.get("FIREBASE_PROJECT_ID")
    FIREBASE_APP_ID = os.environ.get("FIREBASE_APP_ID")

    # Phone OTP demo mode: when ON, the phone tab shows the code on screen instead
    # of sending a real SMS via Firebase. Set PHONE_DEMO_MODE=false in .env to use
    # real Firebase SMS. Defaults to ON so it always works out of the box.
    PHONE_DEMO_MODE = os.environ.get("PHONE_DEMO_MODE", "true").lower() != "false"

    # Email OTP verification (SMTP). With Gmail: SMTP_USER = your gmail,
    # SMTP_PASS = a 16-char App Password (not your normal password).
    # If SMTP_USER/PASS are blank, the code is shown on screen (demo mode).
    SMTP_HOST = os.environ.get("SMTP_HOST", "smtp.gmail.com")
    SMTP_PORT = int(os.environ.get("SMTP_PORT", "587"))
    SMTP_USER = os.environ.get("SMTP_USER")
    SMTP_PASS = os.environ.get("SMTP_PASS")
    MAIL_FROM = os.environ.get("MAIL_FROM") or os.environ.get("SMTP_USER")

    # Business rules
    FREE_DELIVERY_THRESHOLD = 299      # ₹ — orders above this ship free
    DELIVERY_FEE = 25                  # ₹ — flat fee below threshold
    CURRENCY_SYMBOL = "₹"

    # Admin panel login (protects everything under /admin). Override these
    # via environment variables in production — never ship the defaults live.
    ADMIN_USERNAME = os.environ.get("ADMIN_USERNAME", "shaurya johri")
    ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "sai@2006")
