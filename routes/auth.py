"""Google OAuth login — session based.

We deliberately do NOT write the user to the database: on the read-only Vercel
demo the DB isn't writable, so the signed-in user is kept in the Flask session
(a signed cookie). That's enough to greet the user, show their avatar, and
gate any "my account" features. Swap to a User table if you later move to a
persistent database.
"""
import os
from flask import Blueprint, redirect, url_for, session, flash, current_app
from authlib.integrations.flask_client import OAuth

auth_bp = Blueprint("auth", __name__)

oauth = OAuth()


def init_oauth(app):
    """Register the Google provider. Called once from create_app()."""
    oauth.init_app(app)
    oauth.register(
        name="google",
        client_id=app.config.get("GOOGLE_CLIENT_ID"),
        client_secret=app.config.get("GOOGLE_CLIENT_SECRET"),
        server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
        client_kwargs={"scope": "openid email profile"},
    )


@auth_bp.route("/login")
def login():
    if not current_app.config.get("GOOGLE_CLIENT_ID"):
        flash("Google login isn't configured yet (missing GOOGLE_CLIENT_ID).", "error")
        return redirect(url_for("main.home"))
    redirect_uri = url_for("auth.callback", _external=True)
    return oauth.google.authorize_redirect(redirect_uri)


@auth_bp.route("/auth/callback")
def callback():
    try:
        token = oauth.google.authorize_access_token()
    except Exception:
        flash("Sign-in was cancelled or failed. Please try again.", "error")
        return redirect(url_for("main.home"))

    # OpenID Connect returns the profile in the id_token ("userinfo" claim).
    userinfo = token.get("userinfo")
    if not userinfo:
        userinfo = oauth.google.userinfo()

    session["user"] = {
        "name": userinfo.get("name"),
        "given_name": userinfo.get("given_name"),
        "email": userinfo.get("email"),
        "picture": userinfo.get("picture"),
    }
    flash(f"Welcome, {userinfo.get('given_name') or userinfo.get('name') or 'friend'}!", "success")
    return redirect(url_for("main.home"))


@auth_bp.route("/logout")
def logout():
    session.pop("user", None)
    flash("You've been logged out.", "success")
    return redirect(url_for("main.home"))
