import random

from flask import Blueprint, render_template, request, jsonify
from extensions import db
from models import Category, Product, current_season

products_bp = Blueprint("products", __name__, url_prefix="/products")

RELATED_PAGE_SIZE = 4


def _shuffled_related_ids(category_id, exclude_id, seed):
    """Every product id in the category (excluding the current product),
    shuffled deterministically for the given seed so pages 2, 3, ... line up
    with page 1 without repeats — but a fresh seed each page load means the
    order itself is different every time the product page is opened."""
    ids = [
        pid for (pid,) in db.session.query(Product.id)
        .filter_by(category_id=category_id)
        .filter(Product.id != exclude_id)
        .order_by(Product.id)
        .all()
    ]
    random.Random(seed).shuffle(ids)
    return ids


def _products_in_order(id_page):
    """Fetch products for a page of ids and return them in that exact order
    (Product.id.in_(...) does not preserve order on its own)."""
    if not id_page:
        return []
    rows = Product.query.filter(Product.id.in_(id_page)).all()
    order = {pid: i for i, pid in enumerate(id_page)}
    rows.sort(key=lambda p: order[p.id])
    return rows


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

    if season_filter == "seasonal":
        query = query.filter(Product.season != "all-season")
    elif season_filter and season_filter != "all":
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

    # Fresh random seed every time the page is opened, so "You may also like"
    # is shuffled differently each visit/click — not always the same 4 items.
    seed = random.randint(1, 1_000_000)
    related_ids = _shuffled_related_ids(product.category_id, product.id, seed)
    related = _products_in_order(related_ids[:RELATED_PAGE_SIZE])

    return render_template(
        "products/detail.html",
        product=product,
        related=related,
        related_seed=seed,
        related_has_more=len(related_ids) > RELATED_PAGE_SIZE,
    )


@products_bp.route("/<slug>/related")
def related_more(slug):
    """
    Infinite-scroll endpoint for the product detail page: returns the next
    page of "You may also like" items from the same category, continuing the
    same shuffled order (via `seed`) that the page was first rendered with.
    """
    product = Product.query.filter_by(slug=slug).first_or_404()

    seed = request.args.get("seed", type=int) or 0
    offset = max(request.args.get("offset", 0, type=int), 0)
    limit = request.args.get("limit", RELATED_PAGE_SIZE, type=int)

    related_ids = _shuffled_related_ids(product.category_id, product.id, seed)
    page = _products_in_order(related_ids[offset:offset + limit])

    html = render_template("partials/_product_cards_fragment.html", products=page)
    return jsonify({
        "html": html,
        "has_more": offset + limit < len(related_ids),
        "next_offset": offset + limit,
    })

