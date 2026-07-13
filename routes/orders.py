from flask import Blueprint, render_template

orders_bp = Blueprint("orders", __name__)


@orders_bp.route("/checkout")
def checkout():
    """Phase 1 stub. Phase 3 adds the inline name/phone/address form and order placement."""
    return render_template("checkout.html")


@orders_bp.route("/track-order")
def track_order():
    """
    Phase 1 stub. Phase 3 adds a lookup form (order number + phone) and,
    on match, renders the order status — no accounts involved.
    """
    return render_template("orders/track.html", order=None)
