import os
import re
import uuid

from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from werkzeug.utils import secure_filename

from extensions import db
from models import Product, Category

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")

ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "webp", "gif"}


def _allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def _slugify(name):
    slug = name.strip().lower()
    slug = re.sub(r"[^a-z0-9]+", "-", slug)
    return slug.strip("-")


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
    products = Product.query.order_by(Product.id.desc()).all()
    return render_template("admin/dashboard.html", products=products)


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

        product = Product(
            name=name,
            slug=slug,
            category_id=int(category_id),
            price=float(price),
            mrp=float(mrp) if mrp else None,
            unit=unit,
            image=image_path,
            description=description,
            stock=int(stock) if stock else 0,
            is_featured=is_featured,
            is_organic=is_organic,
            season=season,
        )
        db.session.add(product)
        db.session.commit()
        flash(f'"{product.name}" added.', "success")
        return redirect(url_for("admin.dashboard"))

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

        product.name = name
        product.category_id = int(category_id)
        product.price = float(price)
        product.mrp = float(mrp) if mrp else None
        product.unit = unit
        product.description = description
        product.stock = int(stock) if stock else 0
        product.is_featured = is_featured
        product.is_organic = is_organic
        product.season = season

        db.session.commit()
        flash(f'"{product.name}" updated.', "success")
        return redirect(url_for("admin.dashboard"))

    return render_template("admin/product_form.html", categories=categories, product=product, mode="edit")

@admin_bp.route("/product/<int:product_id>/delete", methods=["POST"])
def delete_product(product_id):
    product = Product.query.get_or_404(product_id)
    name = product.name
    db.session.delete(product)
    db.session.commit()
    flash(f'"{name}" deleted.', "success")
    return redirect(url_for("admin.dashboard"))


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
        flash(f'"{product.name}" marked as Out of Stock.', "success")
    else:
        product.stock = 50
        flash(f'"{product.name}" marked back In Stock (set to 50).', "success")

    db.session.commit()
    return redirect(url_for("admin.dashboard"))