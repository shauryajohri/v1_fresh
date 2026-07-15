import logging
from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from extensions import db
from models import Order, OrderItem
from config import Config

orders_bp = Blueprint("orders", __name__)
logger = logging.getLogger(__name__)


def _cart_summary():
    from routes.cart import _get_cart, _build_cart_items
    cart = _get_cart()
    items, subtotal = _build_cart_items(cart)
    delivery = 0 if subtotal >= Config.FREE_DELIVERY_THRESHOLD or subtotal == 0 else Config.DELIVERY_FEE
    return items, subtotal, delivery, round(subtotal + delivery, 2)


@orders_bp.route("/checkout")
def checkout():
    # Checkout requires an account — guests get sent to sign in first, then
    # bounced right back here once they're logged in.
    if not (session.get("user") or {}).get("id"):
        session["login_next"] = url_for("orders.checkout")
        flash("Please sign in to continue to checkout.", "error")
        return redirect(url_for("auth.login", next=url_for("orders.checkout")))

    items, subtotal, delivery, total = _cart_summary()
    return render_template(
        "checkout.html",
        items=items, subtotal=subtotal, delivery_fee=delivery, total=total,
        user=session.get("user") or {},
    )


@orders_bp.route("/checkout/place", methods=["POST"])
def place_order():
    if not (session.get("user") or {}).get("id"):
        flash("Please sign in to place your order.", "error")
        return redirect(url_for("auth.login", next=url_for("orders.checkout")))

    items, subtotal, delivery, total = _cart_summary()
    if not items:
        flash("Your cart is empty.", "error")
        return redirect(url_for("cart.view_cart"))

    name = request.form.get("name", "").strip()
    phone = request.form.get("phone", "").strip()
    address = request.form.get("address", "").strip()
    city = request.form.get("city", "").strip()
    pincode = request.form.get("pincode", "").strip()
    if not (name and phone and address and city and pincode):
        flash("Please fill in all delivery details.", "error")
        return redirect(url_for("orders.checkout"))

    user = session.get("user") or {}
    order = Order(
        user_id=user.get("id"),
        name=name, phone=phone, address_line1=address, city=city, pincode=pincode,
        society=request.form.get("society", ""),
        subtotal=subtotal, delivery_fee=delivery, total=total,
        payment_method=request.form.get("payment_method", "Cash on Delivery"),
    )
    try:
        db.session.add(order)
        db.session.flush()
        for it in items:
            db.session.add(OrderItem(
                order_id=order.id,
                product_id=it["product"].id,
                product_name=it["product"].name,
                unit=it["weight_label"],
                price_at_purchase=it["unit_price"],
                quantity=it["quantity"],
            ))
            # Deduct the ordered quantity from the product's stock (never below 0).
            prod = it["product"]
            prod.stock = max(0, (prod.stock or 0) - it["quantity"])
        db.session.commit()
    except Exception:
        db.session.rollback()
        logger.exception("Failed to save order for user_id=%s", user.get("id"))
        flash("Something went wrong placing your order. Please try again.", "error")
        return redirect(url_for("orders.checkout"))

    # empty the cart (session + the user's saved cart)
    from routes.cart import _save_cart
    _save_cart({})

    flash(f"Order {order.order_number} placed successfully!", "success")
    return redirect(url_for("orders.order_success", order_number=order.order_number))


@orders_bp.route("/order/<order_number>")
def order_success(order_number):
    order = Order.query.filter_by(order_number=order_number).first_or_404()
    return render_template("orders/success.html", order=order)


@orders_bp.route("/orders/my")
def my_orders():
    user = session.get("user")
    if not user or not user.get("id"):
        flash("Please sign in to see your orders.", "error")
        return redirect(url_for("auth.login"))
    orders = Order.query.filter_by(user_id=user["id"]).order_by(Order.created_at.desc()).all()
    total_spent = sum(o.total for o in orders)
    return render_template("orders/my_orders.html", orders=orders, total_spent=total_spent)


@orders_bp.route("/track-order")
def track_order():
    return render_template("orders/track.html", order=None)
