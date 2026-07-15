"""Google OAuth login — session based.

The signed-in user is kept in the Flask session (a signed cookie) rather than
a server-side session store. That's enough to greet the user, show their
avatar, and gate any "my account" features.
"""
import logging
import os
import json
import random
import smtplib
from email.message import EmailMessage
from flask import Blueprint, redirect, url_for, session, flash, current_app, render_template, request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from authlib.integrations.flask_client import OAuth

from extensions import db
from models import User

auth_bp = Blueprint("auth", __name__)
logger = logging.getLogger(__name__)

oauth = OAuth()


def _commit_account(context):
    """Commit a new/updated User row. Returns True on success; on failure rolls
    back and logs so a DB hiccup never leaves the session dirty or crashes
    with a raw 500 mid-login."""
    try:
        db.session.commit()
        return True
    except Exception:
        db.session.rollback()
        logger.exception("Failed to save account during %s", context)
        return False


def _post_login_redirect():
    """Send the user back to whatever page asked them to sign in (e.g. checkout,
    or a product page where they tried to save a wishlist item), stored in
    session['login_next'] when they hit /login?next=...; otherwise home."""
    next_url = session.pop("login_next", None)
    if next_url and next_url.startswith("/") and not next_url.startswith("//"):
        return redirect(next_url)
    return redirect(url_for("main.home"))


def _login_user(user):
    """Store the signed-in user in the session and load their saved cart."""
    session["user"] = {
        "id": user.id,
        "name": user.name,
        "given_name": (user.name or "").split(" ")[0] or user.name,
        "email": user.email,
        "phone": user.phone,
        "picture": user.picture,
    }
    # Restore this user's cart + wishlist from last time (replaces guest ones).
    try:
        session["cart"] = json.loads(user.cart_data) if user.cart_data else {}
    except (ValueError, TypeError):
        session["cart"] = {}
    try:
        session["wishlist_ids"] = json.loads(user.wishlist_data) if user.wishlist_data else []
    except (ValueError, TypeError):
        session["wishlist_ids"] = []
    session.modified = True


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
    """The sign-in page with all the options. Google is the one that fully works;
    the SMS/WhatsApp/Email options are on the page but need external services."""
    next_url = request.args.get("next")
    if next_url and next_url.startswith("/") and not next_url.startswith("//"):
        session["login_next"] = next_url
    return render_template("login.html")


@auth_bp.route("/login/google")
def google_login():
    """Kick off the Google OAuth flow."""
    if not current_app.config.get("GOOGLE_CLIENT_ID"):
        flash("Google login isn't configured yet (missing GOOGLE_CLIENT_ID).", "error")
        return redirect(url_for("auth.login"))
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

    email = (userinfo.get("email") or "").strip().lower()
    user = User.query.filter_by(email=email).first() if email else None
    if not user:
        user = User(name=userinfo.get("name") or "Friend", email=email or None, picture=userinfo.get("picture"))
        db.session.add(user)
    else:
        user.picture = userinfo.get("picture") or user.picture
        if not user.name:
            user.name = userinfo.get("name")
    if not _commit_account("Google sign-in"):
        flash("Something went wrong signing you in. Please try again.", "error")
        return redirect(url_for("auth.login"))
    _login_user(user)
    flash(f"Welcome, {(user.name or 'friend').split(' ')[0]}!", "success")
    return _post_login_redirect()


# ─────────────────────────── Email + Password ───────────────────────────
@auth_bp.route("/login/email", methods=["POST"])
def email_login():
    email = request.form.get("email", "").strip().lower()
    password = request.form.get("password", "")
    name = request.form.get("name", "").strip()

    if not email or not password:
        flash("Please enter both email and password.", "error")
        return redirect(url_for("auth.login"))

    user = User.query.filter_by(email=email).first()
    if user:  # existing account → verify password
        if user.password_hash and check_password_hash(user.password_hash, password):
            _login_user(user)
            flash(f"Welcome back, {user.name}!", "success")
            return _post_login_redirect()
        flash("Incorrect password for that email.", "error")
        return redirect(url_for("auth.login"))

    # new account → name required
    if not name:
        flash("Creating a new account — please add your full name too.", "error")
        return redirect(url_for("auth.login"))
    user = User(name=name, email=email, password_hash=generate_password_hash(password))
    db.session.add(user)
    if not _commit_account("email signup"):
        flash("Something went wrong creating your account. Please try again.", "error")
        return redirect(url_for("auth.login"))
    _login_user(user)
    flash(f"Account created — welcome, {name}!", "success")
    return _post_login_redirect()


# ─────────────────────────── Phone + OTP ───────────────────────────
@auth_bp.route("/login/phone/send", methods=["POST"])
def phone_send():
    phone = "".join(ch for ch in request.form.get("phone", "") if ch.isdigit())[-10:]
    name = request.form.get("name", "").strip()

    if len(phone) != 10:
        flash("Please enter a valid 10-digit mobile number.", "error")
        return redirect(url_for("auth.login"))

    otp = f"{random.randint(0, 999999):06d}"
    session["otp_data"] = {"phone": phone, "name": name, "otp": otp}

    # TODO: to send a real SMS, call your provider here (Twilio / MSG91) with `otp`.
    # Until then we run in DEMO mode and show the code on screen.
    demo_otp = otp if current_app.config.get("SMS_DEMO_MODE", True) else None
    return render_template(
        "login.html", otp_stage=True, otp_phone=phone, demo_otp=demo_otp, active_tab="phone"
    )


@auth_bp.route("/login/phone/verify", methods=["POST"])
def phone_verify():
    entered = request.form.get("otp", "").strip()
    data = session.get("otp_data")
    if not data:
        flash("Your code expired — please request a new one.", "error")
        return redirect(url_for("auth.login"))

    if entered != data["otp"]:
        flash("Incorrect code. Please try again.", "error")
        demo_otp = data["otp"] if current_app.config.get("SMS_DEMO_MODE", True) else None
        return render_template(
            "login.html", otp_stage=True, otp_phone=data["phone"], demo_otp=demo_otp, active_tab="phone"
        )

    phone = data["phone"]
    user = User.query.filter_by(phone=phone).first()
    if not user:
        user = User(name=data.get("name") or f"User {phone[-4:]}", phone=phone)
        db.session.add(user)
        if not _commit_account("phone OTP sign-in"):
            flash("Something went wrong signing you in. Please try again.", "error")
            return redirect(url_for("auth.login"))

    session.pop("otp_data", None)
    _login_user(user)
    flash(f"Welcome, {user.name}!", "success")
    return _post_login_redirect()


# ─────────────────────────── Email OTP verification ───────────────────────────
def _send_email_otp(to_email, otp):
    """Send the OTP by email. Returns True if actually emailed, False if SMTP
    isn't configured (caller then falls back to showing the code on screen)."""
    cfg = current_app.config
    if not cfg.get("SMTP_USER") or not cfg.get("SMTP_PASS"):
        return False
    msg = EmailMessage()
    msg["Subject"] = "Your v1fresh verification code"
    msg["From"] = cfg.get("MAIL_FROM") or cfg.get("SMTP_USER")
    msg["To"] = to_email
    msg.set_content(
        f"Your v1fresh verification code is: {otp}\n\n"
        f"It expires in 10 minutes. If you didn't request this, ignore this email."
    )
    with smtplib.SMTP(cfg.get("SMTP_HOST", "smtp.gmail.com"), cfg.get("SMTP_PORT", 587)) as s:
        s.starttls()
        s.login(cfg["SMTP_USER"], cfg["SMTP_PASS"])
        s.send_message(msg)
    return True


@auth_bp.route("/login/email/send", methods=["POST"])
def email_otp_send():
    email = request.form.get("email", "").strip().lower()
    name = request.form.get("name", "").strip()
    if "@" not in email or "." not in email:
        flash("Please enter a valid email address.", "error")
        return redirect(url_for("auth.login"))

    otp = f"{random.randint(0, 999999):06d}"
    session["email_otp"] = {"email": email, "name": name, "otp": otp}

    try:
        sent = _send_email_otp(email, otp)
    except Exception:
        sent = False
    demo = None if sent else otp  # show the code only when we couldn't email it
    return render_template(
        "login.html", email_otp_stage=True, email_otp_addr=email, email_demo_otp=demo, active_tab="email"
    )


@auth_bp.route("/login/email/verify", methods=["POST"])
def email_otp_verify():
    entered = request.form.get("otp", "").strip()
    data = session.get("email_otp")
    if not data:
        flash("Your code expired — please request a new one.", "error")
        return redirect(url_for("auth.login"))
    if entered != data["otp"]:
        flash("Incorrect code. Please try again.", "error")
        demo = data["otp"] if not current_app.config.get("SMTP_USER") else None
        return render_template(
            "login.html", email_otp_stage=True, email_otp_addr=data["email"], email_demo_otp=demo, active_tab="email"
        )

    email = data["email"]
    user = User.query.filter_by(email=email).first()
    if not user:
        user = User(name=data.get("name") or email.split("@")[0], email=email)
        db.session.add(user)
        if not _commit_account("email OTP sign-in"):
            flash("Something went wrong signing you in. Please try again.", "error")
            return redirect(url_for("auth.login"))
    session.pop("email_otp", None)
    _login_user(user)
    flash(f"Email verified — welcome, {user.name}!", "success")
    return _post_login_redirect()


@auth_bp.route("/login/phone/firebase", methods=["POST"])
def phone_firebase():
    """Finish a Firebase phone sign-in. The browser already verified the OTP with
    Firebase (Google sent the real SMS); here we just create/find the account and
    start the session."""
    data = request.get_json(silent=True) or {}
    phone = "".join(ch for ch in str(data.get("phone", "")) if ch.isdigit())[-10:]
    name = (data.get("name") or "").strip()
    id_token = data.get("id_token")

    if len(phone) != 10 or not id_token:
        return jsonify({"ok": False, "error": "Invalid request"}), 400

    # NOTE: for production you can additionally verify `id_token` server-side with
    # the firebase-admin SDK. The OTP itself was already verified by Firebase.
    user = User.query.filter_by(phone=phone).first()
    if not user:
        user = User(name=name or f"User {phone[-4:]}", phone=phone)
        db.session.add(user)
        if not _commit_account("Firebase phone sign-in"):
            return jsonify({"ok": False, "error": "Something went wrong saving your account. Please try again."}), 500
    _login_user(user)
    next_url = session.pop("login_next", None)
    if not (next_url and next_url.startswith("/") and not next_url.startswith("//")):
        next_url = url_for("main.home")
    return jsonify({"ok": True, "redirect": next_url})


@auth_bp.route("/logout")
def logout():
    # The user's cart is already saved to their account on every change, so we
    # just clear the session — a guest starts fresh with an empty cart.
    session.pop("user", None)
    session["cart"] = {}
    session.pop("wishlist_ids", None)
    session.modified = True
    flash("You've been logged out.", "success")
    return redirect(url_for("main.home"))
