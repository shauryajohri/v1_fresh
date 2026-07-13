from flask import Flask, render_template
from werkzeug.middleware.proxy_fix import ProxyFix
from config import Config
from extensions import db
from models import weight_options_for


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Behind Vercel's proxy — trust X-Forwarded-* so url_for(_external) builds
    # correct https URLs (needed for the Google OAuth redirect URI).
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
        }

    @app.errorhandler(404)
    def not_found(e):
        return render_template("errors/404.html"), 404

    @app.errorhandler(500)
    def server_error(e):
        return render_template("errors/500.html"), 500

    with app.app_context():
        db.create_all()

    return app


app = create_app()

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)