import logging
from flask import Flask, render_template
from werkzeug.middleware.proxy_fix import ProxyFix
from config import Config
from extensions import db
from models import weight_options_for

logger = logging.getLogger(__name__)


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Behind a reverse proxy (Render, Railway, etc.) — trust X-Forwarded-* so
    # url_for(_external) builds correct https URLs (needed for the Google
    # OAuth redirect URI).
    app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

    db.init_app(app)
    app.jinja_env.globals["weight_options_for"] = weight_options_for

    # Google OAuth (session-based login)
    from routes.auth import auth_bp, init_oauth
    init_oauth(app)

    # Register blueprints
    from routes.main import main_bp
    from routes.products import products_bp
    from routes.cart import cart_bp
    from routes.orders import orders_bp
    from routes.admin import admin_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(products_bp)
    app.register_blueprint(cart_bp)
    app.register_blueprint(orders_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(auth_bp)

    # Make cart count available in every template without repeating queries everywhere.
    # No accounts in this build, so the cart lives entirely in the Flask session
    # as {product_id (str): quantity}.
    @app.context_processor
    def inject_cart_count():
        from flask import session
        guest_cart = session.get("cart", {})
        return {
            "cart_count": sum(guest_cart.values()),
            "free_delivery_threshold": Config.FREE_DELIVERY_THRESHOLD,
            # Signed-in Google user (or None) — available in every template.
            "current_user": session.get("user"),
            # Raw cart ({ "id|weight": qty }) so cards can show the qty stepper.
            "cart": guest_cart,
            # The signed-in user's saved wishlist (product IDs), or [].
            "user_wishlist": session.get("wishlist_ids", []),
        }

    @app.errorhandler(404)
    def not_found(e):
        return render_template("errors/404.html"), 404

    @app.errorhandler(500)
    def server_error(e):
        return render_template("errors/500.html"), 500

    with app.app_context():
        db.create_all()
        # Lightweight dev migration: add newly-added User columns to an existing
        # 'users' table (SQLite create_all() won't alter existing tables).
        try:
            from sqlalchemy import text
            existing = {row[1] for row in db.session.execute(text("PRAGMA table_info(users)"))}
            if existing:
                if "picture" not in existing:
                    db.session.execute(text("ALTER TABLE users ADD COLUMN picture VARCHAR(500)"))
                if "cart_data" not in existing:
                    db.session.execute(text("ALTER TABLE users ADD COLUMN cart_data TEXT"))
                if "wishlist_data" not in existing:
                    db.session.execute(text("ALTER TABLE users ADD COLUMN wishlist_data TEXT"))
            order_cols = {row[1] for row in db.session.execute(text("PRAGMA table_info(orders)"))}
            if order_cols and "user_id" not in order_cols:
                db.session.execute(text("ALTER TABLE orders ADD COLUMN user_id INTEGER"))
            db.session.commit()
        except Exception:
            db.session.rollback()
            # Don't let a broken migration pass silently — surface it in the
            # logs now, rather than as a confusing "no such column" error
            # the first time some route touches the missing column later.
            logger.exception("Startup DB migration failed — schema may be out of date")

    return app


app = create_app()

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)