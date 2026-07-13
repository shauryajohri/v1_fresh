"""
Run with: python seed.py
Wipes and repopulates categories + products with realistic Indian grocery data.
Order data is intentionally left empty — orders are created only through checkout (Phase 3).
"""
from app import create_app
from extensions import db
from models import Category, Product
from descriptions import DESCRIPTIONS

app = create_app()

# Lightweight keyword-based season tagging — since the original PRODUCTS
# list has no season data, we guess a sensible default from common Indian
# seasonal produce keywords. Anything unmatched stays "all-season".
# You can always override this per-product later from the Admin panel.
WINTER_KEYWORDS = [
    "turnip", "mustard", "bathua", "carrot", "amla", "gooseberry",
    "cauliflower", "peas", "spinach", "fenugreek", "methi", "radish", "beetroot",
]
SUMMER_KEYWORDS = [
    "melon", "kakri", "cucumber", "ash gourd", "papaya", "mango",
    "watermelon", "lychee", "litchi", "muskmelon",
]
MONSOON_KEYWORDS = [
    "corn", "bhindi", "okra", "colocasia", "arbi", "jackfruit", "kundru", "ivy gourd",
]


def guess_season(product_name):
    name_lower = product_name.lower()
    for kw in WINTER_KEYWORDS:
        if kw in name_lower:
            return "winter"
    for kw in SUMMER_KEYWORDS:
        if kw in name_lower:
            return "summer"
    for kw in MONSOON_KEYWORDS:
        if kw in name_lower:
            return "monsoon"
    return "all-season"

CATEGORIES = [
    {"name": "Fruits", "slug": "fruits", "image": "/static/images/cat-fruits.svg", "sort_order": 1},
    {"name": "Vegetables", "slug": "vegetables", "image": "/static/images/cat-vegetables.svg", "sort_order": 2},
    {"name": "Leafy Greens", "slug": "leafy-greens", "image": "/static/images/cat-leafy.svg", "sort_order": 3},
    {"name": "Exotic", "slug": "exotic", "image": "/static/images/cat-exotic.svg", "sort_order": 4},
    {"name": "Dairy & Eggs", "slug": "dairy-eggs", "image": "/static/images/cat-dairy.svg", "sort_order": 6},
]

PRODUCTS = PRODUCTS = [
    # Vegetables
    {"name": "Deshi Garlic (देसी लहसुन)", "category": "vegetables", "price": 80, "mrp": 100, "unit": "kg", "rating": 4.3},
    {"name": "Bhangar Brinjal (भांगर बैंगन)", "category": "vegetables", "price": 35, "mrp": 45, "unit": "kg", "rating": 4.1},
    {"name": "Green Zucchini (हरी ज़ुकीनी)", "category": "exotic", "price": 80, "mrp": 100, "unit": "kg", "rating": 4.2, "image": "/static/images/products/green-zucchini.webp"},
    {"name": "Broccoli (ब्रोकली)", "category": "exotic", "price": 90, "mrp": 110, "unit": "piece", "rating": 4.3, "organic": True, "image": "/static/images/products/broccoli.webp"},
    {"name": "Small Green Brinjal (हरे छोटे बैंगन)", "category": "vegetables", "price": 38, "mrp": 48, "unit": "kg", "rating": 4.0, "image": "/static/images/products/green-brinjal.webp"},
    {"name": "Colocasia Leaves (अरबी के पत्ते)", "category": "leafy-greens", "price": 20, "mrp": 28, "unit": "bunch", "rating": 4.1, "image": "/static/images/products/colocasia-leaves.webp"},
    {"name": "Tender Coconut (नारियल वाला पानी)", "category": "fruits", "price": 50, "mrp": 65, "unit": "piece", "rating": 4.5, "image": "/static/images/products/tender-coconut.webp"},
    {"name": "Purple Yam / Ratalu (रतालू)", "category": "vegetables", "price": 55, "mrp": 70, "unit": "kg", "rating": 4.2},
    {"name": "Broad Beans Pods (बाकला की फली)", "category": "vegetables", "price": 45, "mrp": 58, "unit": "kg", "rating": 4.1},
    {"name": "Kohlrabi (गांठ गोभी)", "category": "exotic", "price": 40, "mrp": 55, "unit": "kg", "rating": 4.0},
    {"name": "Karonda / Natal Plum (करौंदा)", "category": "exotic", "price": 60, "mrp": 80, "unit": "kg", "rating": 4.1},
    {"name": "Teasel Gourd / Kakrol (काकरोल)", "category": "exotic", "price": 55, "mrp": 70, "unit": "kg", "rating": 4.0},
    {"name": "Thick Pickle Chilli (मोटी मिर्च)", "category": "vegetables", "price": 50, "mrp": 65, "unit": "kg", "rating": 4.0},
    {"name": "Lotus Stem (कमल ककड़ी)", "category": "exotic", "price": 90, "mrp": 115, "unit": "kg", "rating": 4.3},
    {"name": "Turnip (शलजम)", "category": "vegetables", "price": 28, "mrp": 38, "unit": "kg", "rating": 4.0},
    {"name": "Kakri / Long Melon (ककड़ी)", "category": "vegetables", "price": 30, "mrp": 40, "unit": "kg", "rating": 4.1},
    {"name": "Ash Gourd / White Pumpkin (सफेद पेठा)", "category": "vegetables", "price": 30, "mrp": 40, "unit": "kg", "rating": 4.0},
    {"name": "Hill Potato / Pahadi Aloo (पहाड़ी आलू)", "category": "vegetables", "price": 45, "mrp": 58, "unit": "kg", "rating": 4.2},
    {"name": "Water Chestnut / Singhada (सिंघाड़ा)", "category": "exotic", "price": 60, "mrp": 80, "unit": "kg", "rating": 4.2},
    {"name": "Chipsona Potato (चिपसोना आलू)", "category": "vegetables", "price": 35, "mrp": 45, "unit": "kg", "rating": 4.1},
    {"name": "Dill Leaves (सोया का साग)", "category": "leafy-greens", "price": 15, "mrp": 22, "unit": "bunch", "rating": 4.1},
    {"name": "Red & Yellow Capsicum (लाल पीली शिमला मिर्च)", "category": "exotic", "price": 120, "mrp": 150, "unit": "kg", "rating": 4.4},
    {"name": "Malabar Spinach / Poi Greens (पोई का साग)", "category": "leafy-greens", "price": 18, "mrp": 25, "unit": "bunch", "rating": 4.0},
    {"name": "Mustard Greens (सरसों का साग)", "category": "leafy-greens", "price": 20, "mrp": 28, "unit": "bunch", "rating": 4.2},
    {"name": "Water Spinach / Karmi Saag (करमी का साग)", "category": "leafy-greens", "price": 18, "mrp": 25, "unit": "bunch", "rating": 4.0},
    {"name": "Bathua Greens (बथुआ का साग)", "category": "leafy-greens", "price": 18, "mrp": 25, "unit": "bunch", "rating": 4.1},
    {"name": "Red Amaranth Leaves (लाल चौलाई साग)", "category": "leafy-greens", "price": 18, "mrp": 25, "unit": "bunch", "rating": 4.1},
    {"name": "Green Amaranth Leaves (हरी चौलाई साग)", "category": "leafy-greens", "price": 18, "mrp": 25, "unit": "bunch", "rating": 4.0},
    {"name": "Raw Papaya (कच्चा पपीता)", "category": "vegetables", "price": 30, "mrp": 40, "unit": "kg", "rating": 4.1},
    {"name": "Elephant Foot Yam / Jimikand (जिमीकंद)", "category": "vegetables", "price": 60, "mrp": 80, "unit": "kg", "rating": 4.1},
    {"name": "Indian Gooseberry / Amla (आंवला)", "category": "fruits", "price": 50, "mrp": 65, "unit": "kg", "rating": 4.3},
    {"name": "Ripe Pumpkin (पका कद्दू)", "category": "vegetables", "price": 28, "mrp": 38, "unit": "kg", "rating": 4.0},
    {"name": "Cowpea Beans / Yardlong Beans (लोबिया की फली)", "category": "vegetables", "price": 40, "mrp": 52, "unit": "kg", "rating": 4.1},
    {"name": "Cluster Beans / Guar Pods (ग्वार की फली)", "category": "vegetables", "price": 38, "mrp": 50, "unit": "kg", "rating": 4.0},
    {"name": "Kundru / Ivy Gourd (कुंदरू)", "category": "vegetables", "price": 35, "mrp": 45, "unit": "kg", "rating": 4.1},
    {"name": "Hybrid Cucumber (हाइब्रिड खीरा)", "category": "vegetables", "price": 30, "mrp": 40, "unit": "kg", "rating": 4.2},
    {"name": "Red Carrot / Lal Gajar (लाल गाजर)", "category": "vegetables", "price": 45, "mrp": 58, "unit": "kg", "rating": 4.3},
    {"name": "Long Bottle Gourd / Lambi Lauki (लंबी लौकी)", "category": "vegetables", "price": 30, "mrp": 40, "unit": "kg", "rating": 4.0},
    {"name": "Hybrid Tomato (टमाटर)", "category": "vegetables", "price": 30, "mrp": 42, "unit": "kg", "rating": 4.2, "featured": True},
    {"name": "Small Round Brinjal / Bharwan Baingan (भरवां बैंगन)", "category": "vegetables", "price": 40, "mrp": 52, "unit": "kg", "rating": 4.1},
    {"name": "Round Brinjal / Gol Baingan (गोल बैंगन)", "category": "vegetables", "price": 38, "mrp": 48, "unit": "kg", "rating": 4.1},
    {"name": "Colocasia / Taro Root / Arbi (अरबी)", "category": "vegetables", "price": 40, "mrp": 52, "unit": "kg", "rating": 4.1},
    {"name": "Broad Beans / Sem ki Phali", "category": "vegetables", "price": 42, "mrp": 55, "unit": "kg", "rating": 4.1},
    {"name": "Raw Mango / Kacche Aam (कच्चे आम)", "category": "fruits", "price": 40, "mrp": 55, "unit": "kg", "rating": 4.2},
    {"name": "Red Potato / Red Aloo (लाल आलू)", "category": "vegetables", "price": 35, "mrp": 45, "unit": "kg", "rating": 4.1},
    {"name": "Deshi Pointed Gourd / Deshi Parwal (देसी परवल)", "category": "vegetables", "price": 45, "mrp": 58, "unit": "kg", "rating": 4.2},
    {"name": "Peas (मटर)", "category": "vegetables", "price": 60, "mrp": 78, "unit": "kg", "rating": 4.3},
    {"name": "Cauliflower (फूलगोभी)", "category": "vegetables", "price": 40, "mrp": 52, "unit": "piece", "rating": 4.1, "featured": True},
    {"name": "Parwal / Pointed Gourd (परवल)", "category": "vegetables", "price": 45, "mrp": 58, "unit": "kg", "rating": 4.1},
    {"name": "Ridge Gourd / Turai (तोरई)", "category": "vegetables", "price": 30, "mrp": 40, "unit": "kg", "rating": 4.0},
    {"name": "Jackfruit Raw / Kathal (कटहल)", "category": "vegetables", "price": 35, "mrp": 48, "unit": "kg", "rating": 4.2},
    {"name": "Pumpkin / Kaddu (कद्दू)", "category": "vegetables", "price": 28, "mrp": 38, "unit": "kg", "rating": 4.0},
    {"name": "Beetroot / Chukandar (चुकंदर)", "category": "vegetables", "price": 38, "mrp": 50, "unit": "kg", "rating": 4.2},
    {"name": "Drumstick / Sahjan (सहजन)", "category": "vegetables", "price": 50, "mrp": 65, "unit": "kg", "rating": 4.2},
    {"name": "Ladyfinger / Bhindi (भिंडी)", "category": "vegetables", "price": 40, "mrp": 52, "unit": "kg", "rating": 4.2, "featured": True},
    {"name": "Raw Banana (कच्चा केला)", "category": "vegetables", "price": 30, "mrp": 40, "unit": "kg", "rating": 4.1},
    {"name": "Tinda / Round Gourd (टिंडा)", "category": "vegetables", "price": 35, "mrp": 45, "unit": "kg", "rating": 4.0},
    {"name": "Fresh Turmeric / Haldi (ताज़ी हल्दी)", "category": "vegetables", "price": 60, "mrp": 80, "unit": "kg", "rating": 4.3},
    {"name": "Sweet Potato / Shakarkand (शकरकंद)", "category": "vegetables", "price": 35, "mrp": 48, "unit": "kg", "rating": 4.2},
    {"name": "Garlic / Mota Lehsun (मोटा लहसुन)", "category": "vegetables", "price": 100, "mrp": 130, "unit": "kg", "rating": 4.4},
    {"name": "Green Chilli / Hari Mirch (हरी मिर्च)", "category": "vegetables", "price": 40, "mrp": 55, "unit": "kg", "rating": 4.2},
    {"name": "Spring Onion / Hara Pyaz (हरा प्याज)", "category": "vegetables", "price": 30, "mrp": 40, "unit": "bunch", "rating": 4.2},
    {"name": "Ginger / Adrak (अदरक)", "category": "vegetables", "price": 80, "mrp": 100, "unit": "kg", "rating": 4.3},
    {"name": "Lemon / Nimbu (नीम्बू)", "category": "fruits", "price": 60, "mrp": 80, "unit": "kg", "rating": 4.3},
    {"name": "Mint / Pudina (पुदीना)", "category": "leafy-greens", "price": 10, "mrp": 15, "unit": "bunch", "rating": 4.4},
    {"name": "Orange Carrot / Gajar (गाजर)", "category": "vegetables", "price": 45, "mrp": 58, "unit": "kg", "rating": 4.3},
    {"name": "Cabbage / Patta Gobi (पत्ता गोभी)", "category": "vegetables", "price": 28, "mrp": 38, "unit": "kg", "rating": 4.1},
    {"name": "Brinjal / Baingan (बैंगन)", "category": "vegetables", "price": 38, "mrp": 48, "unit": "kg", "rating": 4.1},
    {"name": "Curry Leaves / Kadi Patta (कढ़ी पत्ता)", "category": "leafy-greens", "price": 15, "mrp": 22, "unit": "bunch", "rating": 4.3},
    {"name": "Sweet Corn (मक्का)", "category": "vegetables", "price": 25, "mrp": 35, "unit": "piece", "rating": 4.3},
    {"name": "Methi / Fenugreek Leaves (मेथी)", "category": "leafy-greens", "price": 18, "mrp": 25, "unit": "bunch", "rating": 4.2},
    {"name": "Mushroom Button (मशरूम)", "category": "vegetables", "price": 80, "mrp": 100, "unit": "kg", "rating": 4.3},
    {"name": "Bottle Gourd / Lauki (लौकी)", "category": "vegetables", "price": 30, "mrp": 40, "unit": "kg", "rating": 4.0},
    {"name": "Bitter Gourd / Karela (करेला)", "category": "vegetables", "price": 40, "mrp": 52, "unit": "kg", "rating": 4.1},
    {"name": "English Cucumber / Kheera (खीरा)", "category": "vegetables", "price": 30, "mrp": 40, "unit": "kg", "rating": 4.2},
    {"name": "Radish / Mooli (मूली)", "category": "vegetables", "price": 25, "mrp": 35, "unit": "kg", "rating": 4.0},
    {"name": "French Beans (फ्रेंच बींस)", "category": "vegetables", "price": 50, "mrp": 65, "unit": "kg", "rating": 4.2},
    {"name": "Onion (प्याज)", "category": "vegetables", "price": 35, "mrp": 45, "unit": "kg", "rating": 4.3, "featured": True},
    {"name": "Spinach / Palak (पालक)", "category": "leafy-greens", "price": 20, "mrp": 28, "unit": "bunch", "rating": 4.3, "featured": True, "organic": True},
    {"name": "Coriander / Dhaniya (धनिया)", "category": "leafy-greens", "price": 12, "mrp": 18, "unit": "bunch", "rating": 4.5, "featured": True},
    {"name": "Green Capsicum / Shimla Mirch (शिमला मिर्च)", "category": "vegetables", "price": 60, "mrp": 78, "unit": "kg", "rating": 4.3},
    {"name": "Deshi Tomato (टमाटर)", "category": "vegetables", "price": 28, "mrp": 38, "unit": "kg", "rating": 4.2},

    # Fruits
    {"name": "Sugarcane / Ganna (गन्ना)", "category": "fruits", "price": 30, "mrp": 40, "unit": "piece", "rating": 4.2},
    {"name": "Indian Jujube / Ber (बेर)", "category": "fruits", "price": 40, "mrp": 55, "unit": "kg", "rating": 4.2},
    {"name": "Watermelon (तरबूज)", "category": "fruits", "price": 25, "mrp": 35, "unit": "kg", "rating": 4.4, "featured": True},
    {"name": "Apple (सेब)", "category": "fruits", "price": 180, "mrp": 220, "unit": "kg", "rating": 4.5, "featured": True},
    {"name": "Banana (केला)", "category": "fruits", "price": 45, "mrp": 58, "unit": "dozen", "rating": 4.5, "featured": True},
    {"name": "Jamun (जामुन)", "category": "fruits", "price": 80, "mrp": 100, "unit": "kg", "rating": 4.4},
    {"name": "Guava (अमरूद)", "category": "fruits", "price": 50, "mrp": 65, "unit": "kg", "rating": 4.3},
    {"name": "Mango (आम)", "category": "fruits", "price": 120, "mrp": 150, "unit": "kg", "rating": 4.7, "featured": True},
    {"name": "Coconut / Nariyal (नारियल)", "category": "fruits", "price": 45, "mrp": 58, "unit": "piece", "rating": 4.4},
    {"name": "Pear / Nashpati (नाशपाती)", "category": "fruits", "price": 90, "mrp": 115, "unit": "kg", "rating": 4.3},
    {"name": "Chikoo / Sapota (चीकू)", "category": "fruits", "price": 60, "mrp": 78, "unit": "kg", "rating": 4.3},
    {"name": "Lychee (लीची)", "category": "fruits", "price": 80, "mrp": 100, "unit": "kg", "rating": 4.5},
    {"name": "Muskmelon / Kharbooja (खरबूजा)", "category": "fruits", "price": 35, "mrp": 48, "unit": "kg", "rating": 4.3},
    {"name": "Sweet Lime / Mosambi (मौसम्बी)", "category": "fruits", "price": 70, "mrp": 90, "unit": "kg", "rating": 4.4},
    {"name": "Passion Fruit (पैशन फ्रूट)", "category": "exotic", "price": 150, "mrp": 190, "unit": "piece", "rating": 4.4},
    {"name": "Kiwi (कीवी)", "category": "exotic", "price": 30, "mrp": 40, "unit": "piece", "rating": 4.5},
    {"name": "Blueberry (ब्लूबेरी)", "category": "exotic", "price": 350, "mrp": 420, "unit": "piece", "rating": 4.7},
    {"name": "Strawberry (स्ट्रॉबेरी)", "category": "exotic", "price": 120, "mrp": 150, "unit": "kg", "rating": 4.6},
    {"name": "Avocado (एवोकाडो)", "category": "exotic", "price": 110, "mrp": 140, "unit": "piece", "rating": 4.6, "featured": True},
    {"name": "Pineapple / Ananas (अनानास)", "category": "fruits", "price": 60, "mrp": 80, "unit": "piece", "rating": 4.4},
    {"name": "Black Grapes (अंगूर - काले)", "category": "fruits", "price": 80, "mrp": 100, "unit": "kg", "rating": 4.4},
    {"name": "Orange / Santra (संतरा)", "category": "fruits", "price": 70, "mrp": 90, "unit": "kg", "rating": 4.4},
    {"name": "Papaya (पपीता)", "category": "fruits", "price": 35, "mrp": 45, "unit": "kg", "rating": 4.3},
    {"name": "Green Grapes (अंगूर - हरे)", "category": "fruits", "price": 90, "mrp": 115, "unit": "kg", "rating": 4.5},
    {"name": "Safeda Mango (आम सफेदा)", "category": "fruits", "price": 100, "mrp": 130, "unit": "kg", "rating": 4.5},
    {"name": "Shimla Apple (सेब - शिमला)", "category": "fruits", "price": 200, "mrp": 250, "unit": "kg", "rating": 4.6},
    {"name": "Pomegranate / Anaar (अनार)", "category": "fruits", "price": 160, "mrp": 200, "unit": "kg", "rating": 4.7, "featured": True},
    {"name": "Dragon Fruit (ड्रैगन फ्रूट)", "category": "exotic", "price": 180, "mrp": 220, "unit": "piece", "rating": 4.5},
    {"name": "Normal Potato / Aloo (आलू)", "category": "vegetables", "price": 28, "mrp": 36, "unit": "kg", "rating": 4.1, "featured": True},
]


# ---------------------------------------------------------------------------
# Explicit product -> image mapping.
# Values are filenames inside static/images/products/renamed/ (the folder your
# classifier wrote, where each file is prefixed with its predicted produce
# class). Any product NOT in this map falls back to placeholder.svg.
# Add a line here whenever you add/point a new photo, then re-run: python seed.py
# ---------------------------------------------------------------------------
IMAGE_DIR = "/static/images/products/renamed/"

IMAGE_MAP = {
    # NOTE: filenames come from the classifier and are almost all mislabeled,
    # so every entry below was chosen by eye from what the photo ACTUALLY shows.

    # --- Vegetables ---
    "Deshi Garlic (देसी लहसुन)": "cucumber_swab.png",            # garlic bulbs
    "Garlic / Mota Lehsun (मोटा लहसुन)": "cucumber_zucchini.jpg", # garlic bulbs
    "Bhangar Brinjal (भांगर बैंगन)": "jalepeno_baingan.jpg",     # long purple brinjal
    "Brinjal / Baingan (बैंगन)": "garlic_lotion.jpg",           # long purple brinjal
    "Round Brinjal / Gol Baingan (गोल बैंगन)": "jalepeno_baingan.jpg",
    "Small Green Brinjal (हरे छोटे बैंगन)": "cucumber_mortar_2.jpg", # small purple brinjal
    "Small Round Brinjal / Bharwan Baingan (भरवां बैंगन)": "cucumber_mortar_2.jpg",
    "Green Zucchini (हरी ज़ुकीनी)": "cucumber_cucumber_4.png",   # cucumber (zucchini-like)
    "Hybrid Cucumber (हाइब्रिड खीरा)": "cucumber_cucumber_2.png",
    "English Cucumber / Kheera (खीरा)": "cucumber_cucumber_4.png",
    "Kakri / Long Melon (ककड़ी)": "cucumber_cucumber_2.png",
    "Deshi Pointed Gourd / Deshi Parwal (देसी परवल)": "cucumber_cucumber_3.jpg", # small striped gourd
    "Parwal / Pointed Gourd (परवल)": "cucumber_cucumber_2.jpg",
    "Kundru / Ivy Gourd (कुंदरू)": "cucumber_cucumber_2.jpg",
    "Teasel Gourd / Kakrol (काकरोल)": "cucumber_cucumber_3.jpg",
    "Tinda / Round Gourd (टिंडा)": "cucumber_cucumber_3.jpg",
    "Ridge Gourd / Turai (तोरई)": "cucumber_cucumber_5.png",     # long ridged gourd
    "Bitter Gourd / Karela (करेला)": "cucumber_ear.jpg",         # bumpy bitter gourd
    "Bottle Gourd / Lauki (लौकी)": "banana_lauki.jpg",           # pale-green bottle gourd
    "Long Bottle Gourd / Lambi Lauki (लंबी लौकी)": "pear_granny_smith_4.jpg",
    "Ash Gourd / White Pumpkin (सफेद पेठा)": "watermelon_acorn_squash.jpg", # round green gourd
    "Broccoli (ब्रोकली)": "lettuce_broccoli.jpg",
    "Cauliflower (फूलगोभी)": "cauliflower_cauliflower.png",
    "Cabbage / Patta Gobi (पत्ता गोभी)": "cabbage_head_cabbage_2.png",
    "Colocasia Leaves (अरबी के पत्ते)": "cabbage_head_cabbage.jpg", # broad green leaves
    "Tender Coconut (नारियल वाला पानी)": "apple_granny_smith_2.jpg", # green coconuts
    "Broad Beans Pods (बाकला की फली)": "soy beans_matar.png",    # broad beans in basket
    "Broad Beans / Sem ki Phali": "soy beans_matar.png",
    "French Beans (फ्रेंच बींस)": "lettuce_head_cabbage_2.jpg",   # green beans
    "Kohlrabi (गांठ गोभी)": "turnip_head_cabbage_3.jpg",         # green-white bulbs
    "Turnip (शलजम)": "turnip_head_cabbage.png",                  # white turnips + greens
    "Red & Yellow Capsicum (लाल पीली शिमला मिर्च)": "bell pepper_multicolor paper.jpg",
    "Red Carrot / Lal Gajar (लाल गाजर)": "carrot_knot.jpg",      # red carrots
    "Orange Carrot / Gajar (गाजर)": "carrot_french_loaf_5.jpg",  # orange carrots
    "Spring Onion / Hara Pyaz (हरा प्याज)": "corn_hair_slide.jpg", # spring onions
    "Dill Leaves (सोया का साग)": "corn_pot_2.png",               # feathery dill greens
    "Red Amaranth Leaves (लाल चौलाई साग)": "beetroot_velvet.png", # red/purple leafy
    "Beetroot / Chukandar (चुकंदर)": "beetroot_head_cabbage_4.jpg", # red beets
    "Sweet Corn (मक्का)": "sweetcorn_ear.png",
    "Ginger / Adrak (अदरक)": "eggplant_buckeye.png",             # ginger root
    "Fresh Turmeric / Haldi (ताज़ी हल्दी)": "eggplant_blue berry.jpg", # orange turmeric
    "Green Chilli / Hari Mirch (हरी मिर्च)": "soy beans_cucumber.jpg", # green chillies
    "Thick Pickle Chilli (मोटी मिर्च)": "spinach_hamper_3.jpg",  # green chillies in basket
    "Onion (प्याज)": "onion_hamper_6.jpg",                       # red onions
    "Peas (मटर)": "peas_cucumber_3.png",                         # pea pods
    "Normal Potato / Aloo (आलू)": "potato_dough.png",
    "Red Potato / Red Aloo (लाल आलू)": "sweetpotato_pomegranate.jpg", # red-skin potatoes
    "Hill Potato / Pahadi Aloo (पहाड़ी आलू)": "potato_french_loaf.jpg",
    "Chipsona Potato (चिपसोना आलू)": "potato_dough_2.png",
    "Radish / Mooli (मूली)": "raddish_french_loaf.png",          # white radish
    "Spinach / Palak (पालक)": "spinach_head_cabbage_6.jpg",      # dark leafy spinach
    "Curry Leaves / Kadi Patta (कढ़ी पत्ता)": "spinach_pot_3.jpg", # curry leaves on stem
    "Methi / Fenugreek Leaves (मेथी)": "lettuce_pot_2.jpg",      # leafy green bunch
    "Coriander / Dhaniya (धनिया)": "lettuce_broom_2.jpg",        # coriander bunch
    "Mint / Pudina (पुदीना)": "lettuce_pot.jpg",                 # herb bunches
    "Sweet Potato / Shakarkand (शकरकंद)": "sweetpotato_french_loaf_3.jpg", # orange sweet potato
    "Ripe Pumpkin (पका कद्दू)": "sweetpotato_spaghetti_squash.png", # orange pumpkin
    "Pumpkin / Kaddu (कद्दू)": "sweetpotato_spaghetti_squash.png",
    "Hybrid Tomato (टमाटर)": "tomato_strawberry_5.jpg",
    "Deshi Tomato (टमाटर)": "tomato_strawberry_5.jpg",
    "Raw Banana (कच्चा केला)": "banana_kacha_banana.jpg",        # green raw bananas
    "Raw Mango / Kacche Aam (कच्चे आम)": "ginger_butternut_squash.jpg", # green mango

    # --- Fruits ---
    "Apple (सेब)": "apple_granny_smith_3.png",                   # red apples
    "Shimla Apple (सेब - शिमला)": "apple_granny_smith_5.jpg",
    "Banana (केला)": "banana_banana.jpg",                        # ripe bananas
    "Mango (आम)": "mango_orange_2.jpg",                          # ripe mango
    "Safeda Mango (आम सफेदा)": "mango_strawberry.jpg",
    "Watermelon (तरबूज)": "watermelon_cucumber_4.jpg",           # cut watermelon
    "Muskmelon / Kharbooja (खरबूजा)": "ginger_french_loaf_4.jpg", # cantaloupe
    "Pineapple / Ananas (अनानास)": "pineapple_pineapple.jpg",
    "Sugarcane / Ganna (गन्ना)": "pineapple_vase.jpg",           # sugarcane stalks
    "Pomegranate / Anaar (अनार)": "pomegranate_pomegranate_2.jpg",
    "Orange / Santra (संतरा)": "orange_orange.jpg",
    "Lemon / Nimbu (नीम्बू)": "lemon_lemon_4.jpg",               # yellow lemon
    "Sweet Lime / Mosambi (मौसम्बी)": "lemon_lemon_2.jpg",       # green-yellow citrus
    "Pear / Nashpati (नाशपाती)": "pear_lemon.jpg",               # green pears
    "Papaya (पपीता)": "pear_spaghetti_squash.jpg",               # cut papaya
    "Lychee (लीची)": "apple_strawberry_2.jpg",                   # lychees
    "Coconut / Nariyal (नारियल)": "onion_mortar.jpg",            # brown coconut
    "Indian Jujube / Ber (बेर)": "mango_fig_2.jpg",              # green ber/jujube
    "Black Grapes (अंगूर - काले)": "eggplant_fig.jpg",           # black grapes
    "Green Grapes (अंगूर - हरे)": "eggplant_shopping_basket_2.png", # green grapes

    # --- Exotic ---
    "Kiwi (कीवी)": "kiwi_baseball.jpg",
    "Blueberry (ब्लूबेरी)": "garlic_conch.jpg",                  # blueberries in basket

    # --- Newly added real photos (2026-07-13) — filenames match the produce ---
    "Green Amaranth Leaves (हरी चौलाई साग)": "green_amaranth_leaves.png",
    "Indian Gooseberry / Amla (आंवला)": "amla.png",
    "Avocado (एवोकाडो)": "avocado.jpeg",
    "Bathua Greens (बथुआ का साग)": "bathua.png",
    "Chikoo / Sapota (चीकू)": "chikoo.jpeg",
    "Cluster Beans / Guar Pods (ग्वार की फली)": "cluster_beans.jpeg",
    "Drumstick / Sahjan (सहजन)": "drumstick.png",
    "Green Capsicum / Shimla Mirch (शिमला मिर्च)": "green_capsicum.png",
    "Guava (अमरूद)": "guava.jpeg",
    "Jamun (जामुन)": "jamun.png",
    "Elephant Foot Yam / Jimikand (जिमीकंद)": "jimikand.jpeg",
    "Jackfruit Raw / Kathal (कटहल)": "kathal.png",
    "Ladyfinger / Bhindi (भिंडी)": "ladyfinger.png",
    "Lotus Stem (कमल ककड़ी)": "lotus_stem.png",
    "Mustard Greens (सरसों का साग)": "mustard_greens.png",
    "Passion Fruit (पैशन फ्रूट)": "passion_fruit.png",
    "Malabar Spinach / Poi Greens (पोई का साग)": "poi_greens.png",
    "Purple Yam / Ratalu (रतालू)": "purple_yam.png",
    "Raw Papaya (कच्चा पपीता)": "raw_papaya.png",
    "Strawberry (स्ट्रॉबेरी)": "strawberry.jpeg",
    "Water Chestnut / Singhada (सिंघाड़ा)": "water_chestnut.png",
    "Water Spinach / Karmi Saag (करमी का साग)": "water_spinach.png",
    "Cowpea Beans / Yardlong Beans (लोबिया की फली)": "yardlong_beans.png",
    "Colocasia / Taro Root / Arbi (अरबी)": "arbi.jpg",
    "Mushroom Button (मशरूम)": "mushroom.png",
}


def resolve_image(name):
    """Return the mapped product image URL, or the placeholder if unmapped."""
    filename = IMAGE_MAP.get(name)
    if filename:
        return IMAGE_DIR + filename
    return "/static/images/placeholder.svg"


def slugify(name):
    return (
        name.lower()
        .replace("(", "").replace(")", "").replace(",", "")
        .replace("&", "and").replace("/", "-").replace(" ", "-")
    )

def seed():
    with app.app_context():
        print("Dropping and recreating all tables…")
        db.drop_all()
        db.create_all()

        slug_to_id = {}
        for cat in CATEGORIES:
            c = Category(name=cat["name"], slug=cat["slug"], image=cat["image"], sort_order=cat["sort_order"])
            db.session.add(c)
            db.session.flush()
            slug_to_id[cat["slug"]] = c.id
        print(f"Inserted {len(CATEGORIES)} categories.")

        for p in PRODUCTS:
            cat_slug = p["category"]
            slug = slugify(p["name"])
            product = Product(
                name=p["name"],
                slug=slug,
                category_id=slug_to_id[cat_slug],
                price=p["price"],
                mrp=p.get("mrp"),
                unit=p["unit"],
                image=resolve_image(p["name"]),
                description=DESCRIPTIONS.get(
                    p["name"],
                    f"Fresh {p['name'].split('(')[0].strip()}, sourced same morning and quality-checked before dispatch.",
                ),
                stock=100,
                is_featured=p.get("featured", False),
                is_organic=p.get("organic", False),
                rating=p.get("rating", 4.5),
                season=guess_season(p["name"]),
            )
            db.session.add(product)

        db.session.commit()
        print(f"Inserted {len(PRODUCTS)} products.")
        print("Seed complete.")

if __name__ == "__main__":
    seed()
