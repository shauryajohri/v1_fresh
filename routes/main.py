from flask import Blueprint, render_template, Response
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
    "combo-packs": "Curated combos, priced to save you more",
    "dairy-eggs": "Fresh dairy and eggs delivered daily",
}


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

    # One "spotlight" per category, right after Shop by Category, each
    # showing up to 6 products from that category.
    category_spotlights = []
    for cat in categories:
        cat_products = (
            Product.query.filter_by(category_id=cat.id)
            .order_by(Product.id)
            .limit(6)
            .all()
        )
        if cat_products:
            category_spotlights.append({
                "category": cat,
                "subtitle": CATEGORY_SPOTLIGHT_SUBTITLES.get(cat.slug, ""),
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
