import random
import string
from datetime import datetime, timezone, timedelta
from extensions import db

# India Standard Time (UTC+5:30, no DST) — used to pick the current season by
# the real local date, so Seasonal Picks update automatically as months change.
IST = timezone(timedelta(hours=5, minutes=30))


# Weight/size chips shown on product cards, and the fraction of the product's
# listed price (which is always the *full unit* price, e.g. price per kg,
# price per dozen) that each chip is worth. Both the product card template
# and the cart pricing logic (routes/cart.py) use this same table, so the
# price shown on a card always matches what actually gets charged in the cart.
WEIGHT_OPTIONS = {
    "kg": [("250g", 0.25), ("500g", 0.5), ("1kg", 1.0)],
    "gram": [("100g", 1.0)],
    "piece": [("1 pc", 1.0), ("2 pcs", 2.0)],
    "bunch": [("1 bunch", 1.0)],
    "dozen": [("6 pcs", 0.5), ("1 dozen", 1.0)],
    "pack": [("1 pack", 1.0)],
}

# Extra chips shown only on the product detail page — a wider set than the
# compact card view has room for, for units where buyers often want to jump
# straight to a bigger quantity.
DETAIL_WEIGHT_OPTIONS = {
    "piece": [("1 pc", 1.0), ("2 pcs", 2.0), ("5 pcs", 5.0)],
}

# Per-product overrides for products that shouldn't get the full set of chips
# for their unit (e.g. sugarcane is sold as a single stalk, so it shouldn't
# offer a "2 pcs" combo the way broccoli/coconut/etc. do). Keyed by slug so
# it only affects that one product, not every product sharing the same unit.
PRODUCT_WEIGHT_OVERRIDES = {
    "sugarcane---ganna-गन्ना": [("1 pc", 1.0)],
}


def weight_options_for(unit, detail=False, slug=None):
    """List of (label, fraction) chips to show for a given product unit.
    Pass detail=True on the product detail page for the extended list
    (falls back to the normal/compact list if no extended list exists).
    Pass slug to apply a per-product override, if one exists."""
    if slug and slug in PRODUCT_WEIGHT_OVERRIDES:
        return PRODUCT_WEIGHT_OVERRIDES[slug]
    if detail and unit in DETAIL_WEIGHT_OPTIONS:
        return DETAIL_WEIGHT_OPTIONS[unit]
    return WEIGHT_OPTIONS.get(unit, [(unit, 1.0)])


def weight_fraction(unit, label):
    """Fraction of the base unit price that a given chip label is worth."""
    options = WEIGHT_OPTIONS.get(unit, [(unit, 1.0)]) + DETAIL_WEIGHT_OPTIONS.get(unit, [])
    for opt_label, fraction in options:
        if opt_label == label:
            return fraction
    return 1.0

def default_weight_label(unit):
    return weight_options_for(unit)[0][0]


class Category(db.Model):
    __tablename__ = "categories"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    slug = db.Column(db.String(80), unique=True, nullable=False)
    image = db.Column(db.String(255), nullable=False, default="")
    sort_order = db.Column(db.Integer, default=0)

    products = db.relationship("Product", backref="category", lazy=True)

    def __repr__(self):
        return f"<Category {self.name}>"


class Product(db.Model):
    __tablename__ = "products"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    slug = db.Column(db.String(120), unique=True, nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey("categories.id"), nullable=False)

    price = db.Column(db.Float, nullable=False)           # current selling price
    mrp = db.Column(db.Float, nullable=True)               # original/strike-through price
    unit = db.Column(db.String(30), nullable=False, default="kg")  # kg, dozen, piece, bunch, gram
    image = db.Column(db.String(255), nullable=False, default="")
    description = db.Column(db.Text, nullable=True)
    stock = db.Column(db.Integer, nullable=False, default=100)
    is_featured = db.Column(db.Boolean, default=False)
    is_organic = db.Column(db.Boolean, default=False)
    season = db.Column(db.String(20), nullable=False, default="all-season")  # winter, summer, monsoon, all-season
    rating = db.Column(db.Float, default=4.5)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<Product {self.name}>"

    @property
    def discount_percent(self):
        if self.mrp and self.mrp > self.price:
            return round(((self.mrp - self.price) / self.mrp) * 100)
        return 0

    @property
    def in_stock(self):
        return self.stock > 0


def current_season():
    """
    India-appropriate season buckets, based on today's month (IST):
    Winter: Nov-Feb, Summer: Mar-Jun, Monsoon: Jul-Oct.
    """
    month = datetime.now(IST).month
    if month in (11, 12, 1, 2):
        return "winter"
    elif month in (3, 4, 5, 6):
        return "summer"
    else:
        return "monsoon"

def generate_order_number():
    """e.g. V1F4K9X2 — short, public-facing, used for order lookup instead of accounts."""
    suffix = "".join(random.choices(string.ascii_uppercase + string.digits, k=6))
    return f"V1F{suffix}"


class Order(db.Model):
    """
    No accounts in this build — an order is identified by its order_number
    and looked up later using order_number + phone (see routes/orders.py).
    """
    __tablename__ = "orders"

    id = db.Column(db.Integer, primary_key=True)
    order_number = db.Column(db.String(20), unique=True, nullable=False, default=generate_order_number)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)  # set if logged in

    # contact + shipping details, collected directly at checkout (no saved address book)
    name = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    address_line1 = db.Column(db.String(255), nullable=False)
    society = db.Column(db.String(120), nullable=True)
    city = db.Column(db.String(80), nullable=False)
    pincode = db.Column(db.String(10), nullable=False)

    subtotal = db.Column(db.Float, nullable=False)
    delivery_fee = db.Column(db.Float, nullable=False, default=0)
    total = db.Column(db.Float, nullable=False)

    status = db.Column(db.String(30), default="Placed")  # Placed, Packed, Out for Delivery, Delivered, Cancelled
    payment_method = db.Column(db.String(30), default="Cash on Delivery")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    items = db.relationship("OrderItem", backref="order", lazy=True, cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Order {self.order_number}>"

class OrderItem(db.Model):
    __tablename__ = "order_items"

    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey("orders.id"), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey("products.id"), nullable=True)

    product_name = db.Column(db.String(120), nullable=False)  # snapshot, survives product deletion
    unit = db.Column(db.String(30), nullable=False)
    price_at_purchase = db.Column(db.Float, nullable=False)
    quantity = db.Column(db.Integer, nullable=False)

    product = db.relationship("Product")

    @property
    def line_total(self):
        return round(self.price_at_purchase * self.quantity, 2)


class User(db.Model):
    """Accounts created via email/password or phone-OTP login.
    (Google sign-ins are kept in the session only and don't need a row.)"""
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=True)
    phone = db.Column(db.String(20), unique=True, nullable=True)
    password_hash = db.Column(db.String(255), nullable=True)
    picture = db.Column(db.String(500), nullable=True)      # avatar URL (Google)
    cart_data = db.Column(db.Text, nullable=True)           # saved cart as JSON
    wishlist_data = db.Column(db.Text, nullable=True)       # saved wishlist (JSON list of product IDs)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<User {self.email or self.phone}>"