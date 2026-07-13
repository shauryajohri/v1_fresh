from flask import Blueprint, render_template, request
from models import Category, Product, current_season

products_bp = Blueprint("products", __name__, url_prefix="/products")


@products_bp.route("/")
def listing():
    """
    Phase 1: renders all products so the link works end-to-end.
    Phase 2 will add: category filter, search query, sorting, pagination.
    """
    category_slug = request.args.get("category")
    search_query = request.args.get("q", "").strip()
    season_filter = request.args.get("season")
    query = Product.query

    active_category = None
    if category_slug:
        active_category = Category.query.filter_by(slug=category_slug).first()
        if active_category:
            query = query.filter_by(category_id=active_category.id)

    if search_query:
        query = query.filter(Product.name.ilike(f"%{search_query}%"))

    if season_filter and season_filter != "all":
        query = query.filter_by(season=season_filter)

    products = query.order_by(Product.name).all()
    categories = Category.query.order_by(Category.sort_order).all()

    return render_template(
        "products/listing.html",
        products=products,
        categories=categories,
        active_category=active_category,
        active_season=season_filter,
        current_season=current_season(),
    )


@products_bp.route("/<slug>")
def detail(slug):
    product = Product.query.filter_by(slug=slug).first_or_404()
    related = (
        Product.query.filter_by(category_id=product.category_id)
        .filter(Product.id != product.id)
        .limit(4)
        .all()
    )
    return render_template("products/detail.html", product=product, related=related)
