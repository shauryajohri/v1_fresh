import logging
import os
import re
import uuid

from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app, session
from werkzeug.utils import secure_filename
from werkzeug.security import check_password_hash

from extensions import db
from models import Product, Category, Admin

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")
logger = logging.getLogger(__name__)

ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "webp", "gif"}


@admin_bp.before_request
def _require_admin_login():
    # Login/logout themselves must stay reachable without a session.
    if request.endpoint in ("admin.login", "admin.logout"):
        return None
    if not session.get("is_admin"):
        session["admin_next"] = request.full_path if request.query_string else request.path
        return redirect(url_for("admin.login"))
    return None


@admin_bp.route("/login", methods=["GET", "POST"])
def login():
    if session.get("is_admin"):
        return redirect(url_for("admin.dashboard"))

    error = None
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        admin = Admin.query.filter_by(username=username).first()
        if admin and check_password_hash(admin.password_hash, password):
            session["is_admin"] = True
            session["admin_id"] = admin.id
            next_url = session.pop("admin_next", None)
            flash("Welcome back!", "success")
            return redirect(next_url or url_for("admin.dashboard"))

        error = "Incorrect username or password."

    return render_template("admin/login.html", error=error)


@admin_bp.route("/logout", methods=["POST"])
def logout():
    session.pop("is_admin", None)
    session.pop("admin_id", None)
    flash("Logged out.", "success")
    return redirect(url_for("admin.login"))


def _allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def _slugify(name):
    slug = name.strip().lower()
    slug = re.sub(r"[^a-z0-9]+", "-", slug)
    return slug.strip("-")


def _resolve_mrp(mrp_raw, price_val):
    """Keep MRP sane: it must be the *higher* original price. If it's left blank,
    0, or (by mistake) lower than the selling price, we fall back to the price
    itself — so there's never a negative/backwards discount."""
    try:
        mrp_val = float(mrp_raw) if mrp_raw not in (None, "") else 0.0
    except (TypeError, ValueError):
        mrp_val = 0.0
    return mrp_val if mrp_val > price_val else price_val


def _save_uploaded_image(file_storage):
    """
    Saves an uploaded image into static/images/products/ with a unique
    filename, and returns the DB-ready path (e.g. /static/images/products/xyz.jpg).
    Returns None if no valid file was provided.
    """
    if not file_storage or file_storage.filename == "":
        return None
    if not _allowed_file(file_storage.filename):
        return None

    ext = file_storage.filename.rsplit(".", 1)[1].lower()
    unique_name = f"{uuid.uuid4().hex}.{ext}"
    safe_name = secure_filename(unique_name)

    upload_dir = os.path.join(current_app.static_folder, "images", "products")
    os.makedirs(upload_dir, exist_ok=True)

    file_storage.save(os.path.join(upload_dir, safe_name))
    return f"/static/images/products/{safe_name}"


@admin_bp.route("/")
def dashboard():
    # Admin opens on the Customers view by default.
    return redirect(url_for("admin.customers"))


@admin_bp.route("/products")
def products():
    cat_slug = request.args.get("category")
    search_query = request.args.get("q", "").strip()
    page = request.args.get("page", 1, type=int)

    categories = Category.query.order_by(Category.sort_order).all()
    slug_to_cat = {c.slug: c for c in categories}

    query = Product.query
    active_category = None
    if cat_slug in slug_to_cat:
        active_category = slug_to_cat[cat_slug]
        query = query.filter_by(category_id=active_category.id)
    else:
        cat_slug = None
    if search_query:
        query = query.filter(Product.name.ilike(f"%{search_query}%"))

    pagination = query.order_by(Product.id.desc()).paginate(page=page, per_page=10, error_out=False)
    return render_template(
        "admin/products.html",
        products=pagination.items,
        pagination=pagination,
        categories=categories,
        active_category=cat_slug,
        search_query=search_query,
        active_view="products",
    )


@admin_bp.route("/customers")
def customers():
    from models import User, Order
    from sqlalchemy import func
    search_query = request.args.get("q", "").strip()
    page = request.args.get("page", 1, type=int)

    query = User.query
    if search_query:
        query = query.filter(db.or_(
            User.name.ilike(f"%{search_query}%"),
            User.email.ilike(f"%{search_query}%"),
        ))
    pagination = query.order_by(User.id.desc()).paginate(page=page, per_page=10, error_out=False)

    counts = dict(db.session.query(Order.user_id, func.count(Order.id)).group_by(Order.user_id).all())
    customer_rows = [{"user": u, "orders": counts.get(u.id, 0)} for u in pagination.items]
    return render_template(
        "admin/customers.html",
        customers=customer_rows,
        pagination=pagination,
        search_query=search_query,
        active_view="customers",
    )


@admin_bp.route("/customer/<int:user_id>")
def customer_detail(user_id):
    from models import User, Order
    user = User.query.get_or_404(user_id)
    orders = Order.query.filter_by(user_id=user.id).order_by(Order.created_at.desc()).all()
    total_spent = sum(o.total for o in orders)
    return render_template(
        "admin/customer_detail.html", user=user, orders=orders, total_spent=total_spent,
        active_view="customers",
    )


@admin_bp.route("/product/new", methods=["GET", "POST"])
def new_product():
    categories = Category.query.order_by(Category.sort_order).all()

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        category_id = request.form.get("category_id")
        price = request.form.get("price")
        mrp = request.form.get("mrp")
        unit = request.form.get("unit", "kg")
        stock = request.form.get("stock", 0)
        description = request.form.get("description", "")
        is_featured = bool(request.form.get("is_featured"))
        is_organic = bool(request.form.get("is_organic"))
        season = request.form.get("season", "all-season")

        if not name or not category_id or not price:
            flash("Name, category, and price are required.", "error")
            return render_template("admin/product_form.html", categories=categories, product=None, mode="new")

        image_path = _save_uploaded_image(request.files.get("image_file"))
        if not image_path:
            image_path = "/static/images/placeholder.svg"

        base_slug = _slugify(name)
        slug = base_slug
        i = 1
        while Product.query.filter_by(slug=slug).first():
            i += 1
            slug = f"{base_slug}-{i}"

        price_val = float(price)
        mrp_val = _resolve_mrp(mrp, price_val)

        product = Product(
            name=name,
            slug=slug,
            category_id=int(category_id),
            price=price_val,
            mrp=mrp_val,
            unit=unit,
            image=image_path,
            description=description,
            stock=int(stock) if stock else 0,
            is_featured=is_featured,
            is_organic=is_organic,
            season=season,
        )
        db.session.add(product)
        try:
            db.session.commit()
        except Exception:
            db.session.rollback()
            logger.exception("Failed to add product %r", name)
            flash("Something went wrong saving this product — please try again.", "error")
            return render_template("admin/product_form.html", categories=categories, product=None, mode="new")

        flash(f'"{product.name}" added.', "success")
        return redirect(url_for("admin.products"))

    return render_template("admin/product_form.html", categories=categories, product=None, mode="new")


@admin_bp.route("/product/<int:product_id>/edit", methods=["GET", "POST"])
def edit_product(product_id):
    product = Product.query.get_or_404(product_id)
    categories = Category.query.order_by(Category.sort_order).all()

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        category_id = request.form.get("category_id")
        price = request.form.get("price")
        mrp = request.form.get("mrp")
        unit = request.form.get("unit", "kg")
        stock = request.form.get("stock", 0)
        description = request.form.get("description", "")
        is_featured = bool(request.form.get("is_featured"))
        is_organic = bool(request.form.get("is_organic"))
        season = request.form.get("season", "all-season")

        if not name or not category_id or not price:
            flash("Name, category, and price are required.", "error")
            return render_template("admin/product_form.html", categories=categories, product=product, mode="edit")

        new_image_path = _save_uploaded_image(request.files.get("image_file"))
        if new_image_path:
            product.image = new_image_path

        price_val = float(price)
        product.name = name
        product.category_id = int(category_id)
        product.price = price_val
        product.mrp = _resolve_mrp(mrp, price_val)
        product.unit = unit
        product.description = description
        product.stock = int(stock) if stock else 0
        product.is_featured = is_featured
        product.is_organic = is_organic
        product.season = season

        try:
            db.session.commit()
        except Exception:
            db.session.rollback()
            logger.exception("Failed to update product id=%s", product_id)
            flash("Something went wrong saving this product — please try again.", "error")
            return render_template("admin/product_form.html", categories=categories, product=product, mode="edit")

        flash(f'"{product.name}" updated.', "success")
        return redirect(url_for("admin.products"))

    return render_template("admin/product_form.html", categories=categories, product=product, mode="edit")

@admin_bp.route("/product/<int:product_id>/delete", methods=["POST"])
def delete_product(product_id):
    product = Product.query.get_or_404(product_id)
    name = product.name
    db.session.delete(product)
    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        logger.exception("Failed to delete product id=%s", product_id)
        flash("Something went wrong deleting this product — please try again.", "error")
        return redirect(url_for("admin.products"))

    flash(f'"{name}" deleted.', "success")
    return redirect(url_for("admin.products"))


@admin_bp.route("/product/<int:product_id>/toggle-stock", methods=["POST"])
def toggle_stock(product_id):
    """
    Quick one-click toggle from the dashboard table.
    If currently in stock -> set stock to 0 (Out of Stock).
    If currently out of stock -> restock to a sensible default (50),
    since we don't keep a separate "last known stock" value.
    """
    product = Product.query.get_or_404(product_id)

    if product.stock > 0:
        product.stock = 0
        success_message = f'"{product.name}" marked as Out of Stock.'
    else:
        product.stock = 50
        success_message = f'"{product.name}" marked back In Stock (set to 50).'

    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        logger.exception("Failed to toggle stock for product id=%s", product_id)
        flash("Something went wrong updating stock — please try again.", "error")
        return redirect(url_for("admin.products"))

    flash(success_message, "success")
    return redirect(url_for("admin.products"))