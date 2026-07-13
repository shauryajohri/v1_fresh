"""
Auto-generates a distinct, flat-style SVG icon for every product that doesn't
already have a real photo, based on keyword-matching the product name to a
shape + color template. Matches the visual language already used by
static/images/placeholder.svg and cat-*.svg (rounded card background,
solid-color silhouette, small leaf accent).

Run with: python generate_icons.py
Writes:   static/images/products/<slug>.svg  (one per product)
Updates:  seed.py PRODUCTS list image field is NOT edited directly (seed.py
          already defaults unmatched products to placeholder.svg); instead
          this script updates the *live* database directly so it takes
          effect immediately without reseeding, AND writes a
          product_images.py lookup module that seed.py imports so a future
          `python seed.py` keeps these icons too.
"""
import os
import re

from app import create_app
from extensions import db
from models import Product

app = create_app()

OUT_DIR = os.path.join("static", "images", "products")
os.makedirs(OUT_DIR, exist_ok=True)

# ---------------------------------------------------------------------------
# Shape templates. Each returns inner SVG markup for a 200x200 viewBox,
# already centered. `c` = main color, `a` = accent color.
# ---------------------------------------------------------------------------

def leaf_accent(a, x=140, y=48):
    return f'<path d="M{x} {y}c4-14 16-22 28-22-2 13-12 23-24 25z" fill="{a}"/>'


def shape_round(c, a):
    return f'<circle cx="100" cy="112" r="54" fill="{c}"/>' + leaf_accent(a)


def shape_citrus(c, a):
    body = f'<circle cx="100" cy="112" r="54" fill="{c}"/>'
    lines = "".join(
        f'<line x1="100" y1="112" x2="{100+50*__import__("math").cos(ang)}" '
        f'y2="{112+50*__import__("math").sin(ang)}" stroke="{a}" stroke-width="2" opacity="0.35"/>'
        for ang in [0, 1.05, 2.09, 3.14, 4.19, 5.24]
    )
    return body + lines + leaf_accent(a)


def shape_elongated(c, a):
    return (
        f'<path d="M92 40c8-4 18-2 22 8 10 26 10 78-6 108-10 18-30 16-32-4-6-40 2-96 16-112z" fill="{c}"/>'
        + leaf_accent(a, x=88, y=34)
    )


def shape_leafy_bunch(c, a):
    leaves = "".join(
        f'<path d="M100 150 C {70+i*12} {60+ (i%3)*10}, {60+i*14} {40+(i%2)*10}, {95+i*6} {150}" '
        f'fill="{c if i % 2 == 0 else a}" opacity="0.92"/>'
        for i in range(5)
    )
    stem = '<rect x="96" y="140" width="8" height="28" rx="3" fill="#65350f"/>'
    return leaves + stem


def shape_gourd_ridged(c, a):
    body = f'<ellipse cx="100" cy="115" rx="46" ry="58" fill="{c}"/>'
    ridges = "".join(
        f'<path d="M{70+i*12} 62 Q {70+i*12} 115 {70+i*12} 168" stroke="{a}" stroke-width="3" '
        f'fill="none" opacity="0.35"/>'
        for i in range(5)
    )
    return body + ridges + leaf_accent(a, x=118, y=48)


def shape_pod(c, a):
    pod = f'<path d="M50 120c0-30 30-55 65-55s55 20 40 45-45 45-75 45-30-15-30-35z" fill="{c}"/>'
    peas = "".join(
        f'<circle cx="{70+i*22}" cy="{100+(-1)**i*8}" r="10" fill="{a}"/>' for i in range(4)
    )
    return pod + peas


def shape_cluster(c, a):
    import math
    dots = ""
    positions = [(-20, -10), (0, -20), (20, -10), (-30, 10), (-10, 5), (10, 5), (30, 10),
                 (-20, 25), (0, 30), (20, 25), (0, 5)]
    for i, (dx, dy) in enumerate(positions):
        col = c if i % 3 else a
        dots += f'<circle cx="{100+dx}" cy="{115+dy}" r="13" fill="{col}"/>'
    stem = f'<path d="M100 78c4-14 16-22 28-22-2 13-12 23-24 25z" fill="{a}"/>'
    return dots + stem


def shape_banana_bunch(c, a):
    curves = "".join(
        f'<path d="M{75+i*12} 150 C {60+i*12} 100, {70+i*12} 55, {100+i*10} 45 '
        f'C {90+i*12} 90, {90+i*12} 130, {85+i*12} 158 Z" fill="{c if i%2==0 else a}"/>'
        for i in range(3)
    )
    return curves


def shape_cob(c, a):
    body = f'<path d="M100 40c14 0 22 12 22 30v70c0 14-10 22-22 22s-22-8-22-22V70c0-18 8-30 22-30z" fill="{c}"/>'
    kernels = ""
    for row in range(6):
        yy = 58 + row * 15
        for col in range(3):
            xx = 84 + col * 12
            kernels += f'<circle cx="{xx}" cy="{yy}" r="4" fill="{a}" opacity="0.5"/>'
    husk = f'<path d="M78 40c-10 6-16 18-12 30l14-4z" fill="#65a30d"/>'
    return body + kernels + husk


def shape_root_knobby(c, a):
    return (
        f'<path d="M65 95c-8-14 2-30 20-30 6-12 24-16 34-4 16-2 28 12 22 26 10 10 6 30-10 34 '
        f'-2 14-20 22-32 14-14 8-30-2-30-18-10-4-12-16-4-22z" fill="{c}"/>'
        + leaf_accent(a, x=108, y=42)
    )


def shape_layered_round(c, a):
    layers = "".join(
        f'<circle cx="100" cy="112" r="{56-i*10}" fill="{c}" opacity="{0.55+i*0.15}"/>'
        for i in range(4)
    )
    return layers + leaf_accent(a)


def shape_pepper(c, a):
    body = (
        f'<path d="M100 55c-6 0-10 6-8 12-18 4-30 22-28 44 2 22 20 40 40 38s34-20 32-42 '
        f'c-2-20-16-36-36-40z" fill="{c}"/>'
    )
    stem = f'<path d="M96 40c2-8 10-12 16-10-2 8-8 14-16 10z" fill="#15803d"/>'
    return body + stem


def shape_mushroom(c, a):
    cap = f'<path d="M50 100a50 34 0 0 1 100 0z" fill="{c}"/>'
    stem = f'<rect x="88" y="98" width="24" height="55" rx="10" fill="{a}"/>'
    return cap + stem


def shape_potato_blob(c, a):
    body = f'<ellipse cx="100" cy="115" rx="52" ry="42" fill="{c}"/>'
    eyes = "".join(
        f'<circle cx="{78+i*20}" cy="{105+(i%2)*20}" r="3.5" fill="{a}" opacity="0.6"/>'
        for i in range(4)
    )
    return body + eyes


def shape_spiky_crown(c, a):
    body = f'<ellipse cx="100" cy="125" rx="42" ry="50" fill="{c}"/>'
    spikes = "".join(
        f'<path d="M{85+i*10} 78 L{88+i*10} 40 L{93+i*10} 78 Z" fill="{a}"/>' for i in range(4)
    )
    return body + spikes


def shape_kiwi_fuzzy(c, a):
    body = f'<circle cx="100" cy="112" r="52" fill="{c}"/>'
    fuzz = "".join(
        f'<circle cx="{100+40*__import__("math").cos(ang)}" cy="{112+40*__import__("math").sin(ang)}" '
        f'r="2.4" fill="{a}" opacity="0.5"/>'
        for ang in [i * 0.45 for i in range(14)]
    )
    return body + fuzz


def shape_combo_box(c, a):
    crate = f'<rect x="46" y="95" width="108" height="62" rx="8" fill="#92400e"/>'
    slats = "".join(
        f'<rect x="{46+i*22}" y="95" width="4" height="62" fill="#78350f" opacity="0.5"/>'
        for i in range(6)
    )
    items = (
        f'<circle cx="78" cy="92" r="18" fill="{c}"/>'
        f'<circle cx="112" cy="86" r="16" fill="{a}"/>'
        f'<circle cx="128" cy="100" r="14" fill="#facc15"/>'
    )
    return crate + slats + items


BG_TINTS = {
    "green": "#f0fdf4", "red": "#fef2f2", "orange": "#fff7ed", "yellow": "#fefce8",
    "purple": "#faf5ff", "brown": "#fefbe9", "pink": "#fdf2f8", "default": "#f0fdf4",
}

# ---------------------------------------------------------------------------
# Keyword -> (shape_fn, main_color, accent_color, tint_key). Checked in
# order; first substring match on the lowercased English product name wins.
# ---------------------------------------------------------------------------
RULES = [
    # leafy greens
    ("spinach", shape_leafy_bunch, "#16a34a", "#166534", "green"),
    ("palak", shape_leafy_bunch, "#16a34a", "#166534", "green"),
    ("coriander", shape_leafy_bunch, "#22c55e", "#15803d", "green"),
    ("dhaniya", shape_leafy_bunch, "#22c55e", "#15803d", "green"),
    ("mint", shape_leafy_bunch, "#4ade80", "#16a34a", "green"),
    ("pudina", shape_leafy_bunch, "#4ade80", "#16a34a", "green"),
    ("methi", shape_leafy_bunch, "#65a30d", "#3f6212", "green"),
    ("fenugreek", shape_leafy_bunch, "#65a30d", "#3f6212", "green"),
    ("mustard greens", shape_leafy_bunch, "#4d7c0f", "#365314", "green"),
    ("bathua", shape_leafy_bunch, "#65a30d", "#3f6212", "green"),
    ("curry leaves", shape_leafy_bunch, "#166534", "#14532d", "green"),
    ("dill", shape_leafy_bunch, "#4ade80", "#22c55e", "green"),
    ("malabar spinach", shape_leafy_bunch, "#15803d", "#166534", "green"),
    ("water spinach", shape_leafy_bunch, "#15803d", "#166534", "green"),
    ("amaranth", shape_leafy_bunch, "#dc2626", "#16a34a", "red"),
    ("colocasia leaves", shape_leafy_bunch, "#166534", "#14532d", "green"),

    # pods / beans / peas
    ("peas", shape_pod, "#4ade80", "#86efac", "green"),
    ("cluster beans", shape_pod, "#65a30d", "#a3e635", "green"),
    ("guar", shape_pod, "#65a30d", "#a3e635", "green"),
    ("cowpea", shape_pod, "#4d7c0f", "#a3e635", "green"),
    ("yardlong", shape_pod, "#4d7c0f", "#a3e635", "green"),
    ("french beans", shape_pod, "#22c55e", "#bbf7d0", "green"),
    ("broad beans", shape_pod, "#65a30d", "#bbf7d0", "green"),
    ("sem ki phali", shape_pod, "#65a30d", "#bbf7d0", "green"),

    # gourds
    ("bottle gourd", shape_gourd_ridged, "#84cc16", "#65a30d", "green"),
    ("lauki", shape_gourd_ridged, "#84cc16", "#65a30d", "green"),
    ("ridge gourd", shape_gourd_ridged, "#4d7c0f", "#365314", "green"),
    ("turai", shape_gourd_ridged, "#4d7c0f", "#365314", "green"),
    ("ash gourd", shape_gourd_ridged, "#a3e635", "#65a30d", "green"),
    ("white pumpkin", shape_gourd_ridged, "#a3e635", "#65a30d", "green"),
    ("bitter gourd", shape_gourd_ridged, "#3f6212", "#65a30d", "green"),
    ("karela", shape_gourd_ridged, "#3f6212", "#65a30d", "green"),
    ("teasel gourd", shape_gourd_ridged, "#4d7c0f", "#65a30d", "green"),
    ("kakrol", shape_gourd_ridged, "#4d7c0f", "#65a30d", "green"),
    ("tinda", shape_round, "#84cc16", "#4d7c0f", "green"),
    ("round gourd", shape_round, "#84cc16", "#4d7c0f", "green"),
    ("pumpkin", shape_gourd_ridged, "#f97316", "#c2410c", "orange"),
    ("kaddu", shape_gourd_ridged, "#f97316", "#c2410c", "orange"),

    # long / root veg
    ("carrot", shape_elongated, "#f97316", "#166534", "orange"),
    ("gajar", shape_elongated, "#f97316", "#166534", "orange"),
    ("radish", shape_elongated, "#f8fafc", "#166534", "green"),
    ("mooli", shape_elongated, "#f8fafc", "#166534", "green"),
    ("turnip", shape_round, "#f8fafc", "#7c3aed", "purple"),
    ("shaljam", shape_round, "#f8fafc", "#7c3aed", "purple"),
    ("beetroot", shape_round, "#9f1239", "#166534", "red"),
    ("chukandar", shape_round, "#9f1239", "#166534", "red"),
    ("drumstick", shape_elongated, "#4d7c0f", "#365314", "green"),
    ("sahjan", shape_elongated, "#4d7c0f", "#365314", "green"),
    ("cucumber", shape_elongated, "#4ade80", "#166534", "green"),
    ("kheera", shape_elongated, "#4ade80", "#166534", "green"),
    ("kakri", shape_elongated, "#a3e635", "#4d7c0f", "green"),
    ("long melon", shape_elongated, "#a3e635", "#4d7c0f", "green"),
    ("zucchini", shape_elongated, "#4d7c0f", "#365314", "green"),
    ("lotus stem", shape_elongated, "#f5f5dc", "#a16207", "brown"),
    ("water chestnut", shape_root_knobby, "#7c2d12", "#a16207", "brown"),
    ("singhada", shape_root_knobby, "#7c2d12", "#a16207", "brown"),

    # tubers / roots
    ("ginger", shape_root_knobby, "#eab308", "#166534", "yellow"),
    ("adrak", shape_root_knobby, "#eab308", "#166534", "yellow"),
    ("turmeric", shape_root_knobby, "#f59e0b", "#92400e", "yellow"),
    ("haldi", shape_root_knobby, "#f59e0b", "#92400e", "yellow"),
    ("yam", shape_root_knobby, "#7c3aed", "#a16207", "purple"),
    ("ratalu", shape_root_knobby, "#7c3aed", "#a16207", "purple"),
    ("jimikand", shape_root_knobby, "#a16207", "#78350f", "brown"),
    ("sweet potato", shape_potato_blob, "#9a3412", "#7c2d12", "brown"),
    ("shakarkand", shape_potato_blob, "#9a3412", "#7c2d12", "brown"),
    ("potato", shape_potato_blob, "#d4a373", "#92400e", "brown"),
    ("aloo", shape_potato_blob, "#d4a373", "#92400e", "brown"),

    # onion / garlic
    ("spring onion", shape_leafy_bunch, "#a3e635", "#65a30d", "green"),
    ("hara pyaz", shape_leafy_bunch, "#a3e635", "#65a30d", "green"),
    ("onion", shape_round, "#c2410c", "#78350f", "orange"),
    ("pyaz", shape_round, "#c2410c", "#78350f", "orange"),
    ("garlic", shape_cluster, "#f5f5dc", "#e5e5c8", "brown"),
    ("lehsun", shape_cluster, "#f5f5dc", "#e5e5c8", "brown"),

    # brinjal / eggplant
    ("brinjal", shape_elongated, "#6d28d9", "#4c1d95", "purple"),
    ("baingan", shape_round, "#6d28d9", "#4c1d95", "purple"),

    # chillies / capsicum
    ("green capsicum", shape_pepper, "#16a34a", "#166534", "green"),
    ("shimla mirch", shape_pepper, "#16a34a", "#166534", "green"),
    ("red & yellow capsicum", shape_pepper, "#facc15", "#dc2626", "yellow"),
    ("green chilli", shape_pepper, "#22c55e", "#166534", "green"),
    ("hari mirch", shape_pepper, "#22c55e", "#166534", "green"),
    ("thick pickle chilli", shape_pepper, "#dc2626", "#7f1d1d", "red"),

    # tomato
    ("tomato", shape_round, "#dc2626", "#166534", "red"),
    ("टमाटर", shape_round, "#dc2626", "#166534", "red"),

    # cabbage / cauliflower / kohlrabi
    ("cabbage", shape_layered_round, "#65a30d", "#f0fdf4", "green"),
    ("patta gobi", shape_layered_round, "#65a30d", "#f0fdf4", "green"),
    ("cauliflower", shape_layered_round, "#fefce8", "#eab308", "yellow"),
    ("phoolgobi", shape_layered_round, "#fefce8", "#eab308", "yellow"),
    ("kohlrabi", shape_round, "#a3e635", "#4d7c0f", "green"),
    ("gaanth gobi", shape_round, "#a3e635", "#4d7c0f", "green"),

    # corn / mushroom
    ("corn", shape_cob, "#facc15", "#eab308", "yellow"),
    ("makka", shape_cob, "#facc15", "#eab308", "yellow"),
    ("mushroom", shape_mushroom, "#f5f5dc", "#a3a3a3", "brown"),

    # jackfruit / raw fruit-as-veg
    ("jackfruit", shape_root_knobby, "#65a30d", "#3f6212", "green"),
    ("kathal", shape_root_knobby, "#65a30d", "#3f6212", "green"),
    ("raw banana", shape_elongated, "#84cc16", "#4d7c0f", "green"),
    ("kacha kela", shape_elongated, "#84cc16", "#4d7c0f", "green"),
    ("raw papaya", shape_elongated, "#65a30d", "#3f6212", "green"),
    ("raw mango", shape_round, "#65a30d", "#3f6212", "green"),
    ("kacche aam", shape_round, "#65a30d", "#3f6212", "green"),
    ("sugarcane", shape_elongated, "#a3e635", "#4d7c0f", "green"),
    ("ganna", shape_elongated, "#a3e635", "#4d7c0f", "green"),
    ("parwal", shape_elongated, "#4d7c0f", "#365314", "green"),
    ("pointed gourd", shape_elongated, "#4d7c0f", "#365314", "green"),

    # fruits: round / citrus / berries / bunches
    ("watermelon", shape_round, "#16a34a", "#dc2626", "green"),
    ("tarbooj", shape_round, "#16a34a", "#dc2626", "green"),
    ("muskmelon", shape_round, "#eab308", "#a16207", "yellow"),
    ("kharbooja", shape_round, "#eab308", "#a16207", "yellow"),
    ("apple", shape_round, "#dc2626", "#166534", "red"),
    ("seb", shape_round, "#dc2626", "#166534", "red"),
    ("banana", shape_banana_bunch, "#facc15", "#eab308", "yellow"),
    ("kela", shape_banana_bunch, "#facc15", "#eab308", "yellow"),
    ("jamun", shape_cluster, "#4c1d95", "#7c3aed", "purple"),
    ("guava", shape_round, "#a3e635", "#4d7c0f", "green"),
    ("amrud", shape_round, "#a3e635", "#4d7c0f", "green"),
    ("mango", shape_round, "#f97316", "#facc15", "orange"),
    ("aam", shape_round, "#f97316", "#facc15", "orange"),
    ("coconut", shape_round, "#78350f", "#f5f5dc", "brown"),
    ("nariyal", shape_round, "#78350f", "#f5f5dc", "brown"),
    ("pear", shape_elongated, "#a3e635", "#4d7c0f", "green"),
    ("nashpati", shape_elongated, "#a3e635", "#4d7c0f", "green"),
    ("chikoo", shape_round, "#92400e", "#78350f", "brown"),
    ("sapota", shape_round, "#92400e", "#78350f", "brown"),
    ("lychee", shape_cluster, "#dc2626", "#166534", "red"),
    ("lichi", shape_cluster, "#dc2626", "#166534", "red"),
    ("sweet lime", shape_citrus, "#a3e635", "#4d7c0f", "green"),
    ("mosambi", shape_citrus, "#a3e635", "#4d7c0f", "green"),
    ("passion fruit", shape_round, "#7c3aed", "#facc15", "purple"),
    ("kiwi", shape_kiwi_fuzzy, "#65a30d", "#f5f5dc", "green"),
    ("blueberry", shape_cluster, "#3b82f6", "#1d4ed8", "purple"),
    ("strawberry", shape_cluster, "#dc2626", "#16a34a", "red"),
    ("avocado", shape_round, "#4d7c0f", "#365314", "green"),
    ("pineapple", shape_spiky_crown, "#eab308", "#65a30d", "yellow"),
    ("ananas", shape_spiky_crown, "#eab308", "#65a30d", "yellow"),
    ("grapes", shape_cluster, "#7c3aed", "#4c1d95", "purple"),
    ("angoor", shape_cluster, "#7c3aed", "#4c1d95", "purple"),
    ("orange", shape_citrus, "#f97316", "#c2410c", "orange"),
    ("santra", shape_citrus, "#f97316", "#c2410c", "orange"),
    ("papaya", shape_elongated, "#f97316", "#65a30d", "orange"),
    ("dragon fruit", shape_spiky_crown, "#db2777", "#16a34a", "pink"),
    ("pomegranate", shape_round, "#9f1239", "#166534", "red"),
    ("anaar", shape_round, "#9f1239", "#166534", "red"),
    ("gooseberry", shape_round, "#84cc16", "#4d7c0f", "green"),
    ("amla", shape_round, "#84cc16", "#4d7c0f", "green"),
    ("jujube", shape_round, "#a16207", "#4d7c0f", "brown"),
    ("ber", shape_round, "#a16207", "#4d7c0f", "brown"),
    ("karonda", shape_cluster, "#9f1239", "#166534", "red"),
    ("natal plum", shape_cluster, "#9f1239", "#166534", "red"),
    ("lemon", shape_citrus, "#eab308", "#65a30d", "yellow"),
    ("nimbu", shape_citrus, "#eab308", "#65a30d", "yellow"),

    # combo packs
    ("combo", shape_combo_box, "#dc2626", "#f97316", "brown"),
    ("basket", shape_combo_box, "#dc2626", "#f97316", "brown"),
]

CATEGORY_FALLBACK = {
    "vegetables": (shape_round, "#65a30d", "#365314", "green"),
    "fruits": (shape_round, "#f97316", "#facc15", "orange"),
    "leafy-greens": (shape_leafy_bunch, "#22c55e", "#15803d", "green"),
    "exotic": (shape_round, "#7c3aed", "#a16207", "purple"),
    "combo-packs": (shape_combo_box, "#dc2626", "#f97316", "brown"),
    "dairy-eggs": (shape_round, "#fefce8", "#eab308", "yellow"),
}


def english_name(full_name):
    return re.split(r"[\(/]", full_name)[0].strip().lower()


def pick_rule(name, category_slug):
    lname = name.lower()
    for kw, shape_fn, c, a, tint in RULES:
        if kw in lname:
            return shape_fn, c, a, tint
    return CATEGORY_FALLBACK.get(category_slug, (shape_round, "#65a30d", "#365314", "green"))


def build_svg(shape_fn, c, a, tint):
    bg = BG_TINTS.get(tint, BG_TINTS["default"])
    inner = shape_fn(c, a)
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 200">'
        f'<rect width="200" height="200" rx="20" fill="{bg}"/>'
        f"{inner}"
        f"</svg>"
    )


def run():
    with app.app_context():
        products = Product.query.all()
        generated, kept = 0, 0
        for p in products:
            # Keep real photos already uploaded (webp/jpg/png) — only replace
            # placeholder.svg or missing images.
            if p.image and not p.image.endswith("placeholder.svg") and p.image.strip() != "":
                if any(p.image.lower().endswith(ext) for ext in (".webp", ".jpg", ".jpeg", ".png", ".gif")):
                    kept += 1
                    continue

            cat_slug = p.category.slug if p.category else None
            ename = english_name(p.name)
            shape_fn, c, a, tint = pick_rule(ename, cat_slug)
            svg = build_svg(shape_fn, c, a, tint)

            clean_slug = re.sub(r"-+", "-", re.sub(r"[^a-z0-9]+", "-", ename)).strip("-")
            filename = f"{clean_slug}-{p.id}.svg"
            path = os.path.join(OUT_DIR, filename)
            with open(path, "w", encoding="utf-8") as f:
                f.write(svg)

            p.image = f"/static/images/products/{filename}"
            generated += 1

        db.session.commit()
        print(f"Generated {generated} new icon(s). Kept {kept} existing real photo(s).")


if __name__ == "__main__":
    run()
