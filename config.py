import os
import shutil

BASE_DIR = os.path.abspath(os.path.dirname(__file__))


def _resolve_db_uri():
    """Return a SQLAlchemy SQLite URI that is writable in the current environment.

    On Vercel (and any read-only-filesystem host) the app directory is NOT
    writable, so we copy the bundled, pre-seeded database to /tmp once per
    cold start and use that copy. Data written after a cold start (e.g. new
    orders) lives only for the life of that warm instance — this is the
    intended behaviour for the read-only demo deployment.
    """
    bundled = os.path.join(BASE_DIR, "v1fresh.db")

    # VERCEL is set automatically in Vercel's runtime. Fall back to a generic
    # read-only check so this also works on similar hosts.
    on_serverless = bool(os.environ.get("VERCEL"))

    if on_serverless:
        tmp_db = "/tmp/v1fresh.db"
        try:
            if not os.path.exists(tmp_db) and os.path.exists(bundled):
                shutil.copy(bundled, tmp_db)
        except OSError:
            pass
        return "sqlite:///" + tmp_db

    return "sqlite:///" + bundled


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-key-change-in-production")
    SQLALCHEMY_DATABASE_URI = _resolve_db_uri()
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Behind Vercel's proxy the app is served over HTTPS; make url_for(_external)
    # and the OAuth redirect URI use https so they match what Google expects.
    PREFERRED_URL_SCHEME = "https" if os.environ.get("VERCEL") else "http"

    # Google OAuth (set these as environment variables in Vercel / locally)
    GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID")
    GOOGLE_CLIENT_SECRET = os.environ.get("GOOGLE_CLIENT_SECRET")

    # Business rules
    FREE_DELIVERY_THRESHOLD = 299      # ₹ — orders above this ship free
    DELIVERY_FEE = 25                  # ₹ — flat fee below threshold
    CURRENCY_SYMBOL = "₹"
