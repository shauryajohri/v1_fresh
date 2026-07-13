from flask import Blueprint, render_template, session, request, jsonify
from config import Config
from models import Product, weight_fraction, default_weight_label

cart_bp = Blueprint("cart", __name__, url_prefix="/cart")

KEY_SEP = "|"


def _cart_key(product_id, weight_label):
    return f"{product_id}{KEY_SEP}{weight_label}"


def _split_key(cart_key):
    product_id_str, _, weight_label = cart_key.partition(KEY_SEP)
    return product_id_str, weight_label


def _get_cart():
    """
    Cart lives in session as {"<product_id>|<weight_label>": quantity (int)}.
    Each distinct weight selection of the same product is its own line
    (e.g. "12|500g" and "12|1kg" can both be in the cart at once).
    """
    return session.get("cart", {})


def _save_cart(cart):
    session["cart"] = cart
    session.modified = True


def _cart_count(cart):
    return sum(cart.values())


def _unit_price(product, weight_label):
    """The product's listed price is always the full-unit price (e.g. per kg);
    scale it by the chip's fraction (e.g. 500g -> 0.5) to get what's charged."""
    fraction = weight_fraction(product.unit, weight_label)
    return round(product.price * fraction, 2)


def _build_cart_items(cart):
    """
    Turns the raw {"product_id|weight_label": qty} session dict into a list of
    {product, weight_label, quantity, unit_price, line_total} for rendering,
    skipping any product_id that no longer exists (e.g. deleted from catalog).
    Also returns the subtotal so callers don't loop twice.
    """
    items = []
    subtotal = 0.0

    for cart_key, quantity in cart.items():
        product_id_str, weight_label = _split_key(cart_key)
        product = Product.query.get(int(product_id_str)) if product_id_str.isdigit() else None
        if product is None:
            continue
        unit_price = _unit_price(product, weight_label)
        line_total = round(unit_price * quantity, 2)
        subtotal += line_total
        items.append({
            "product": product,
            "weight_label": weight_label,
            "quantity": quantity,
            "unit_price": unit_price,
            "line_total": line_total,
        })

    return items, round(subtotal, 2)


@cart_bp.route("/")
def view_cart():
    cart = _get_cart()
    cart_items, subtotal = _build_cart_items(cart)

    delivery_fee = 0 if subtotal >= Config.FREE_DELIVERY_THRESHOLD or subtotal == 0 else Config.DELIVERY_FEE
    amount_for_free_delivery = max(0, Config.FREE_DELIVERY_THRESHOLD - subtotal)

    return render_template(
        "cart.html",
        cart_items=cart_items,
        subtotal=subtotal,
        delivery_fee=delivery_fee,
        amount_for_free_delivery=amount_for_free_delivery,
        total=round(subtotal + delivery_fee, 2),
    )


@cart_bp.route("/add", methods=["POST"])
def add_to_cart():
    data = request.get_json(silent=True) or {}
    product_id = str(data.get("product_id", ""))
    quantity = data.get("quantity", 1)
    if not isinstance(quantity, int) or quantity < 1:
        quantity = 1

    product = Product.query.get(int(product_id)) if product_id.isdigit() else None
    if product is None:
        return jsonify({"ok": False, "error": "Product not found"}), 404
    if not product.in_stock:
        return jsonify({"ok": False, "error": "Out of stock"}), 400

    weight_label = data.get("weight_label") or default_weight_label(product.unit)

    cart = _get_cart()
    cart_key = _cart_key(product_id, weight_label)
    cart[cart_key] = cart.get(cart_key, 0) + quantity
    _save_cart(cart)

    return jsonify({
        "ok": True,
        "product_id": product_id,
        "weight_label": weight_label,
        "quantity": cart[cart_key],
        "unit_price": _unit_price(product, weight_label),
        "cart_count": _cart_count(cart),
    })


@cart_bp.route("/update", methods=["POST"])
def update_cart():
    data = request.get_json(silent=True) or {}
    product_id = str(data.get("product_id", ""))
    quantity = data.get("quantity")

    if not product_id.isdigit() or not isinstance(quantity, int):
        return jsonify({"ok": False, "error": "Invalid request"}), 400

    product = Product.query.get(int(product_id))
    if product is None:
        return jsonify({"ok": False, "error": "Product not found"}), 404

    weight_label = data.get("weight_label") or default_weight_label(product.unit)

    cart = _get_cart()
    cart_key = _cart_key(product_id, weight_label)

    if quantity <= 0:
        cart.pop(cart_key, None)
    else:
        cart[cart_key] = quantity

    _save_cart(cart)

    # Recompute so the client can repaint line total / subtotal / free-delivery banner in one go
    _, subtotal = _build_cart_items(cart)
    delivery_fee = 0 if subtotal >= Config.FREE_DELIVERY_THRESHOLD or subtotal == 0 else Config.DELIVERY_FEE

    line_total = None
    if cart_key in cart:
        line_total = round(_unit_price(product, weight_label) * cart[cart_key], 2)

    return jsonify({
        "ok": True,
        "product_id": product_id,
        "weight_label": weight_label,
        "quantity": cart.get(cart_key, 0),
        "line_total": line_total,
        "subtotal": subtotal,
        "delivery_fee": delivery_fee,
        "total": round(subtotal + delivery_fee, 2),
        "cart_count": _cart_count(cart),
    })


@cart_bp.route("/remove", methods=["POST"])
def remove_from_cart():
    data = request.get_json(silent=True) or {}
    product_id = str(data.get("product_id", ""))
    weight_label = data.get("weight_label", "")

    cart = _get_cart()
    cart.pop(_cart_key(product_id, weight_label), None)
    _save_cart(cart)

    _, subtotal = _build_cart_items(cart)
    delivery_fee = 0 if subtotal >= Config.FREE_DELIVERY_THRESHOLD or subtotal == 0 else Config.DELIVERY_FEE

    return jsonify({
        "ok": True,
        "product_id": product_id,
        "weight_label": weight_label,
        "subtotal": subtotal,
        "delivery_fee": delivery_fee,
        "total": round(subtotal + delivery_fee, 2),
        "cart_count": _cart_count(cart),
    })