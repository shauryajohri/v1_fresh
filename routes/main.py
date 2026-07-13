from flask import Blueprint, render_template, Response, request
from models import Category, Product, current_season

main_bp = Blueprint("main", __name__)

# Fixed subtitle text per category slug, shown under each category's
# spotlight heading on the homepage (e.g. "Aloo, Pyaz, Tamatar & more...").
# Edit these strings to whatever wording you want per category.
CATEGORY_SPOTLIGHT_SUBTITLES = {
    "vegetables": "Aloo, Pyaz, Tamatar & more at best prices",
    "fruits": "Farm-fresh fruits picked at peak ripeness",
    "leafy-greens": "Crisp greens, harvested same day",
    "exotic": "Exotic picks for your everyday cooking",
    "dairy-eggs": "Fresh dairy and eggs delivered daily",
}

# Homepage spotlight sections, in the order they appear below "Shop by Category".
SPOTLIGHT_ORDER = ["vegetables", "fruits"]


@main_bp.route("/")
def home():
    categories = Category.query.order_by(Category.sort_order).all()
    featured_products = (
        Product.query.filter_by(is_featured=True)
        .order_by(Product.id)
        .limit(8)
        .all()
    )
    season = current_season()
    seasonal_products = (
        Product.query.filter_by(season=season)
        .order_by(Product.id)
        .limit(4)
        .all()
    )

    # Spotlight sections right after "Shop by Category" — Fresh Vegetables,
    # then Fresh Fruits (see SPOTLIGHT_ORDER). "Featured Products" is rendered
    # separately below these in the template.
    cats_by_slug = {c.slug: c for c in categories}
    category_spotlights = []
    for slug in SPOTLIGHT_ORDER:
        cat = cats_by_slug.get(slug)
        if not cat:
            continue
        cat_products = (
            Product.query.filter_by(category_id=cat.id)
            .order_by(Product.id)
            .limit(6)
            .all()
        )
        if cat_products:
            category_spotlights.append({
                "category": cat,
                "subtitle": CATEGORY_SPOTLIGHT_SUBTITLES.get(slug, ""),
                "products": cat_products,
            })

    return render_template(
        "index.html",
        categories=categories,
        featured_products=featured_products,
        seasonal_products=seasonal_products,
        current_season=season,
        category_spotlights=category_spotlights,
    )

@main_bp.route("/wishlist")
def wishlist():
    """Wishlist page. The saved items live in the browser (localStorage), so
    the page shell is rendered here and filled in by JS via /wishlist/cards."""
    return render_template("wishlist.html")


@main_bp.route("/wishlist/cards")
def wishlist_cards():
    """Return the product cards (HTML fragment) for a comma-separated list of
    product IDs, preserving the order they were saved in."""
    raw = request.args.get("ids", "")
    id_list = [int(x) for x in raw.split(",") if x.strip().isdigit()]
    products = []
    if id_list:
        found = {p.id: p for p in Product.query.filter(Product.id.in_(id_list)).all()}
        products = [found[i] for i in id_list if i in found]
    return render_template("partials/_wishlist_cards.html", products=products)


@main_bp.route("/about")
def about():
    return render_template("about.html")


@main_bp.route("/contact")
def contact():
    return render_template("contact.html")


@main_bp.route("/privacy-policy")
def privacy_policy():
    return render_template(
        "policy.html",
        page_title="Privacy Policy",
        page_content="This is a placeholder Privacy Policy page. Full policy content will be added soon.",
    )


@main_bp.route("/terms-and-conditions")
def terms_conditions():
    return render_template(
        "policy.html",
        page_title="Terms & Conditions",
        page_content="This is a placeholder Terms & Conditions page. Full terms will be added soon.",
    )


@main_bp.route("/refund-return-policy")
def refund_policy():
    return render_template(
        "policy.html",
        page_title="Refund & Return Policy",
        page_content="This is a placeholder Refund & Return Policy page. Full policy content will be added soon.",
    )


@main_bp.route("/shipping-policy")
def shipping_policy():
    return render_template(
        "policy.html",
        page_title="Shipping Policy",
        page_content="This is a placeholder Shipping Policy page. Full policy content will be added soon.",
    )


@main_bp.route("/cancellation-policy")
def cancellation_policy():
    return render_template(
        "policy.html",
        page_title="Cancellation Policy",
        page_content="This is a placeholder Cancellation Policy page. Full policy content will be added soon.",
    )


@main_bp.route("/quality-guarantee")
def quality_guarantee():
    return render_template(
        "policy.html",
        page_title="Quality Guarantee",
        page_content="This is a placeholder Quality Guarantee page. Full details will be added soon.",
    )
