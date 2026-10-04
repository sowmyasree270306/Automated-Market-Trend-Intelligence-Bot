# ============================================================
# AUTOMATED MARKET & TREND INTELLIGENCE BOT
# COMPLETE FLASK BACKEND
# ============================================================

from flask import (
    Flask,
    render_template,
    request,
    redirect,
    session,
    jsonify,
    Response,
)
from functools import lru_cache
from urllib.parse import unquote
import os
import re
import sqlite3
import math

import pandas as pd
import requests

try:
    from rapidfuzz import fuzz, process
except ImportError:
    fuzz = None
    process = None


# ============================================================
# FLASK APP
# ============================================================

app = Flask(__name__)

app.secret_key = "market_bot_secret_key_change_this"


# ============================================================
# PROJECT PATHS
# ============================================================

BASE_DIR = os.path.dirname(
    os.path.abspath(__file__)
)

DATASET_DIR = os.path.join(
    BASE_DIR,
    "dataset"
)

DATABASE_PATH = os.path.join(
    BASE_DIR,
    "database.db"
)

ALL_MARKETPLACES_FILE = os.path.join(
    DATASET_DIR,
    "all_marketplaces.csv"
)

AMAZON_FILE = os.path.join(
    DATASET_DIR,
    "amazon.csv"
)

FLIPKART_FILE = os.path.join(
    DATASET_DIR,
    "flipkart.csv"
)

CROMA_FILE = os.path.join(
    DATASET_DIR,
    "croma_products_final.csv"
)

BESTBUY_FILE = os.path.join(
    DATASET_DIR,
    "BestBuy_Products.csv"
)

MAPPING_FILE = os.path.join(
    DATASET_DIR,
    "product_mappings.csv"
)


# ============================================================
# MARKETPLACES
# ============================================================

MARKETPLACES = [
    "amazon",
    "flipkart",
    "croma",
    "bestbuy",
]


MARKETPLACE_DISPLAY = {
    "amazon": "Amazon",
    "flipkart": "Flipkart",
    "croma": "Croma",
    "bestbuy": "Best Buy",
    "best buy": "Best Buy",
    "best_buy": "Best Buy",
}
def normalize_marketplace(val):
    if not val or pd.isna(val):
        return ""
    # Strip spaces, hyphens, and underscores so "Best Buy" -> "bestbuy"
    cleaned = (
        str(val)
        .lower()
        .replace(" ", "")
        .replace("-", "")
        .replace("_", "")
        .strip()
    )
    return cleaned
def normalize_marketplace(val):
    if not val or pd.isna(val):
        return ""
    return str(val).lower().replace(" ", "").replace("-", "").replace("_", "").strip()

# ============================================================
# ACCESSORY WORDS
# ============================================================

ACCESSORY_WORDS = {
    "case",
    "cover",
    "charger",
    "charging",
    "cable",
    "adapter",
    "stand",
    "holder",
    "screen",
    "protector",
    "tempered",
    "glass",
    "film",
    "wire",
    "wireless",
    "powerbank",
    "power",
    "bank",
    "battery",
    "replacement",
    "strap",
    "sleeve",
    "pouch",
    "mount",
    "dock",
    "hub",
    "connector",
    "earphone",
    "earphones",
    "headphone",
    "headphones",
    "earbuds",
    "keyboard",
    "mouse",
    "stylus",
    "pen",
    "skin",
    "car",
    "wall",
    "desk",
    "tripod",
    "holder",
}


# ============================================================
# MAIN PRODUCT WORDS
# ============================================================

PRODUCT_WORDS = {
    "phone",
    "phones",
    "smartphone",
    "smartphones",
    "mobile",
    "mobiles",
    "iphone",
    "ipad",
    "macbook",
    "laptop",
    "laptops",
    "tablet",
    "tablets",
    "watch",
    "watches",
    "television",
    "tv",
    "monitor",
    "monitors",
    "camera",
    "cameras",
    "refrigerator",
    "fridge",
    "washing",
    "machine",
    "airpods",
    "airpod",
    "earbuds",
    "headphones",
    "speaker",
    "speakers",
    "printer",
    "printers",
}


# ============================================================
# BRAND ALIASES
# ============================================================

BRAND_ALIASES = {
    "apple": "apple",
    "iphone": "apple",
    "ipad": "apple",
    "macbook": "apple",
    "airpods": "apple",

    "samsung": "samsung",
    "galaxy": "samsung",

    "redmi": "xiaomi",
    "xiaomi": "xiaomi",

    "poco": "poco",

    "oneplus": "oneplus",

    "vivo": "vivo",

    "oppo": "oppo",

    "realme": "realme",

    "nokia": "nokia",

    "motorola": "motorola",
    "moto": "motorola",

    "google": "google",
    "pixel": "google",

    "lg": "lg",
    "sony": "sony",
    "lenovo": "lenovo",
    "hp": "hp",
    "dell": "dell",
    "asus": "asus",
    "acer": "acer",

    "boat": "boat",
    "noise": "noise",
    "fireboltt": "fire-boltt",
    "fire-boltt": "fire-boltt",
}


# ============================================================
# DATABASE
# ============================================================

def db():

    conn = sqlite3.connect(
        DATABASE_PATH
    )

    conn.row_factory = sqlite3.Row

    return conn


# ============================================================
# SAFE TEXT
# ============================================================

def clean_text(value):

    if value is None:
        return ""

    try:

        if pd.isna(value):
            return ""

    except Exception:
        pass

    return str(value).strip()


# ============================================================
# SAFE FLOAT
# ============================================================

def safe_float(
    value,
    default=0.0
):

    try:

        if value is None:
            return default

        if isinstance(
            value,
            float
        ) and math.isnan(value):

            return default

        text = str(value)

        text = (
            text
            .replace("₹", "")
            .replace("$", "")
            .replace("€", "")
            .replace(",", "")
            .replace("%", "")
            .strip()
        )

        if text == "":
            return default

        return float(text)

    except Exception:

        return default


# ============================================================
# SAFE INTEGER
# ============================================================

def safe_int(
    value,
    default=0
):

    try:

        return int(
            round(
                safe_float(
                    value,
                    default
                )
            )
        )

    except Exception:

        return default


# ============================================================
# NORMALIZE PRODUCT NAME
# ============================================================

def normalize_name(value):

    text = clean_text(
        value
    ).lower()

    text = text.replace(
        "&",
        " and "
    )

    text = re.sub(
        r"[^a-z0-9]+",
        " ",
        text
    )

    text = re.sub(
        r"\s+",
        " ",
        text
    )

    return text.strip()


# ============================================================
# TOKENIZE
# ============================================================

def tokenize(value):

    text = normalize_name(
        value
    )

    if not text:
        return []

    return text.split()


# ============================================================
# MODEL TOKENS
# ============================================================

def extract_model_tokens(
    value
):

    tokens = tokenize(
        value
    )

    models = []

    special_model_words = {
        "pro",
        "max",
        "plus",
        "ultra",
        "mini",
        "air",
        "note",
        "fe",
        "se",
        "lite",
        "prime",
        "neo",
        "5g",
        "4g",
    }

    for token in tokens:

        if re.search(
            r"\d",
            token
        ):

            models.append(
                token
            )

        elif token in special_model_words:

            models.append(
                token
            )

    return models


# ============================================================
# DETECT BRAND
# ============================================================

def detect_brand(
    text
):

    tokens = tokenize(
        text
    )

    for token in tokens:

        if token in BRAND_ALIASES:

            return BRAND_ALIASES[
                token
            ]

    return None


# ============================================================
# ACCESSORY DETECTION
# ============================================================

def contains_accessory(
    text
):

    tokens = set(
        tokenize(text)
    )

    return bool(
        tokens.intersection(
            ACCESSORY_WORDS
        )
    )



# ============================================================
# IMAGE URL
# ============================================================

LOCAL_CROMA_IMAGES = {
    "mxd02hn": "apple_iphone_se_2nd_gen_128gb_mxd02hn_a_black.webp",
    "ua43au9070ulxl": "samsung_9_series_43inch_ua43au9070ulxl.webp",
    "43pft681594": "philips_6800_43inch_43pft6815_94.webp",
    "waj2846din": "bosch_serie6_7_5kg_waj2846din.webp",
    "cscuku18xkytf": "panasonic_ku_1_5ton_cs_cu_ku18xkytf.webp",
}

def _local_model_key(text):
    return re.sub(r"[^a-z0-9]", "", clean_text(text).lower())

def get_croma_local_image(row):
    if normalize_marketplace(row.get("marketplace", "")) != "croma":
        return ""
    fields = [row.get("product_id", ""), row.get("product_name", ""), row.get("model", ""), row.get("sku", "")]
    blob = " ".join(clean_text(x) for x in fields)
    key_blob = _local_model_key(blob)
    for model_key, filename in LOCAL_CROMA_IMAGES.items():
        if model_key in key_blob:
            return "/static/croma_images/" + filename
    return ""

def get_display_image(row):
    local = get_croma_local_image(row)
    return local or get_image_value(row.get("image", ""))

def is_accessory_product(row):
    name = normalize_name(clean_text(row.get("product_name", "")))
    category = normalize_name(clean_text(row.get("category", "")))
    text = f"{name} {category}"
    strong_phrases = [
        "remote control", "tv remote", "remote", "phone case", "mobile case",
        "back cover", "screen protector", "tempered glass", "display protector",
        "charging cable", "usb cable", "data cable", "hdmi cable", "power cable",
        "wall charger", "car charger", "travel adapter", "phone holder", "laptop bag",
        "replacement battery", "camera bag", "tv stand", "wall mount", "protective cover"
    ]
    if any(p in text for p in strong_phrases):
        return True
    accessory_words = {
        "case", "cover", "cable", "charger", "adapter", "protector", "tempered",
        "sleeve", "pouch", "holder", "mount", "stand", "replacement", "skin",
        "bumper", "grip", "strap", "wallet", "accessory", "accessories", "film"
    }
    tokens = set(text.split())
    if tokens & accessory_words:
        return True
    if any(x in category for x in ("accessor", "case", "cover", "charger", "cable", "protector", "remote")):
        return True
    return False

def get_image_value(value):
    text = clean_text(value)

    if not text or text.lower() in {
        "nan", "none", "null", "n/a", "na", "-"
    }:
        return ""

    # Split multiple image URLs without cutting at commas.
    urls = re.split(r"\s*[;|]\s*", text)

    for url in urls:
        url = url.strip().strip("'\"")

        if not url.startswith(("http://", "https://")):
            continue

        # Reject placeholder images and incomplete Croma transformation
        # URLs such as https://media.croma.com/image/upload/f_auto.
        # A usable image URL must contain an actual filename after the
        # transformation parameters (for example, .../v123/product.png).
        path = url.split("?", 1)[0].rstrip("/")
        filename = path.rsplit("/", 1)[-1].lower()

        if filename in {
            "no-product-image.jpg",
            "placeholder.jpg",
            "placeholder.png",
            "f_auto",
            "f_auto,q_auto",
            "f_auto,q_auto,d_croma assets:no-product-image.jpg,h_350,w_350",
        }:
            continue
        if filename in {"image", "upload"} or "." not in filename:
            continue

        # Keep Best Buy's existing HTTPS conversion.
        if url.startswith("http://img.bbystatic.com/"):
            url = "https://" + url[len("http://"):]

        return url

    return ""

# ============================================================
# PRODUCT URL
# ============================================================

def get_product_url(
    value
):

    text = clean_text(
        value
    )

    if not text:
        return "#"

    if text.startswith(
        (
            "http://",
            "https://"
        )
    ):
        return text

    return "#"


# ============================================================
# LOAD CSV
# ============================================================

def load_csv(
    path
):

    if not os.path.exists(
        path
    ):
        return pd.DataFrame()

    try:

        return pd.read_csv(
            path,
            encoding="utf-8",
            low_memory=False
        )

    except UnicodeDecodeError:

        try:

            return pd.read_csv(
                path,
                encoding="latin1",
                low_memory=False
            )

        except Exception as error:

            print(
                f"Could not load {path}: {error}"
            )

            return pd.DataFrame()

    except Exception as error:

        print(
            f"Could not load {path}: {error}"
        )

        return pd.DataFrame()


# ============================================================
# LOAD MAIN MARKETPLACE DATA
# ============================================================

def load_marketplace_data():
    """Load one canonical dataset and fill missing marketplaces from raw CSVs."""
    aliases = {
        "marketplace": ["marketplace", "platform", "source", "store", "website"],
        "product_id": ["product_id", "id", "asin", "sku", "item_id"],
        "product_name": ["product_name", "name", "title", "product", "product_title"],
        "brand": ["brand", "manufacturer", "make"],
        "category": ["category", "product_category", "type"],
        "price": ["price_inr", "discounted_price", "selling_price", "sale_price", "current_price", "price", "final_price"],
        "mrp": ["mrp_inr", "actual_price", "original_price", "original_mrp", "list_price", "regular_price", "mrp", "retail_price"],
        "discount": ["discount", "discount_percentage", "discount_percent", "off"],
        "rating": ["rating", "stars", "average_rating", "customer_rating"],
        "reviews": ["reviews", "rating_count", "ratings_and_reviews", "review_count", "ratings_count", "num_reviews"],
        "currency": ["currency", "currency_code"],
        "image": ["image", "images", "image_url", "img_link", "img", "product_image", "product_image_url", "thumbnail", "image_link"],
        "product_url": ["product_url", "product_link", "link", "url", "web_url"],
        "availability": ["availability", "stock", "status", "availability_status"],
        "price_inr": ["price_inr", "price", "discounted_price", "selling_price", "sale_price", "current_price", "final_price"],
    }

    def standardize(frame, default_market=""):
        if frame is None or frame.empty:
            return pd.DataFrame()
        frame = frame.copy()
        lookup = {re.sub(r"[^a-z0-9]+", "", str(c).lower()): c for c in frame.columns}
        out = pd.DataFrame(index=frame.index)
        for target, choices in aliases.items():
            source = next((lookup.get(re.sub(r"[^a-z0-9]+", "", c.lower())) for c in choices
                           if lookup.get(re.sub(r"[^a-z0-9]+", "", c.lower())) is not None), None)
            out[target] = frame[source] if source is not None else ""
        # Croma's source has name/link/images; Amazon uses discounted_price/img_link.
        if default_market:
            out["marketplace"] = default_market
        out["marketplace"] = out["marketplace"].apply(normalize_marketplace)
        if "price_inr" in out:
            # Amazon and Croma prices are INR. Best Buy remains USD in price and uses
            # its precomputed INR value from the aggregate when available.
            pass
        return out

    combined = load_csv(ALL_MARKETPLACES_FILE)
    frames = []
    if not combined.empty:
        frames.append(standardize(combined))

    # Load source CSVs as well as the aggregate. The aggregate may be older
    # than the latest Amazon/Croma downloads, so do not skip a marketplace
    # merely because it already appears in all_marketplaces.csv.
    import glob
    sources = [
        (AMAZON_FILE, "amazon"),
        (FLIPKART_FILE, "flipkart"),
        (CROMA_FILE, "croma"),
        (BESTBUY_FILE, "bestbuy"),
    ]
    known_paths = {os.path.abspath(path) for path, _ in sources}
    # Discover downloaded marketplace files even when filenames differ slightly.
    auto_patterns = [
        ("amazon", ["amazon*.csv"]),
        ("flipkart", ["flipkart*.csv"]),
        ("croma", ["croma*.csv"]),
        ("bestbuy", ["bestbuy*.csv", "best_buy*.csv", "best buy*.csv"]),
    ]
    for market, patterns in auto_patterns:
        for pattern in patterns:
            for path in sorted(glob.glob(os.path.join(DATASET_DIR, pattern))):
                basename = os.path.basename(path).lower()
                if (os.path.abspath(path) not in known_paths
                        and not basename.startswith(("all_marketplaces", "merged_electronics"))):
                    sources.append((path, market))
                    known_paths.add(os.path.abspath(path))

    for path, market in sources:
        if not os.path.isfile(path):
            continue
        part = load_csv(path)
        if not part.empty:
            frames.append(standardize(part, market))

    if not frames:
        print("WARNING: No marketplace CSV files could be loaded from", DATASET_DIR)
        return pd.DataFrame()
    df = pd.concat(frames, ignore_index=True, sort=False)
    for col in ["marketplace", "product_id", "product_name", "brand", "category", "price", "mrp",
                "discount", "rating", "reviews", "currency", "image", "product_url", "availability", "price_inr"]:
        if col not in df:
            df[col] = ""
    df["marketplace"] = df["marketplace"].apply(normalize_marketplace)
    df = df[df["marketplace"].isin(MARKETPLACES)].copy()
    for col in ["product_name", "brand", "category", "currency", "image", "product_url", "availability", "product_id"]:
        df[col] = df[col].apply(clean_text)
    for col in ["price", "mrp", "discount", "rating", "reviews", "price_inr"]:
        df[col] = df[col].apply(safe_float)
    # Prefer an explicit INR amount; otherwise retain the source selling price.
    df["price"] = df["price_inr"].where(df["price_inr"].gt(0), df["price"])
    df["price_inr"] = df["price_inr"].where(df["price_inr"].gt(0), df["price"])
    df["image"] = df["image"].apply(get_image_value)
    df["product_url"] = df["product_url"].apply(get_product_url)
    df = df[df["product_name"].str.strip().ne("")].copy()
    df["normalized_name"] = df["product_name"].apply(normalize_name)
    df["model_tokens"] = df["product_name"].apply(lambda x: set(extract_model_tokens(x)))
    # Prefer the duplicate record that has a usable image URL. The aggregate
    # file can contain an older/incomplete Croma URL (ending in /f_auto), while
    # the source Croma CSV contains the full image URL for the same product.
    # Sorting before deduplication prevents the older row from hiding it.
    df["_image_quality"] = df["image"].apply(
        lambda value: 1 if get_image_value(value) else 0
    )
    df["_url_quality"] = df["product_url"].apply(
        lambda value: 1 if get_product_url(value) != "#" else 0
    )
    df = df.sort_values(
        by=["_image_quality", "_url_quality"],
        ascending=[False, False],
        kind="stable"
    )
    df = df.drop_duplicates(
        subset=["marketplace", "product_id", "product_name"],
        keep="first"
    )
    df = df.drop(columns=["_image_quality", "_url_quality"], errors="ignore")
    return df.reset_index(drop=True)

marketplace_df = (
    load_marketplace_data()
)


# ============================================================
# DEAL SCORE
# ============================================================

def deal_score(
    row
):

    price = safe_float(
        row.get(
            "price_inr",
            row.get(
                "price",
                0
            )
        )
    )

    discount = max(
        0,
        min(
            100,
            safe_float(
                row.get(
                    "discount",
                    0
                )
            )
        )
    )

    rating = max(
        0,
        min(
            5,
            safe_float(
                row.get(
                    "rating",
                    0
                )
            )
        )
    )

    reviews = max(
        0,
        safe_float(
            row.get(
                "reviews",
                0
            )
        )
    )

    availability = (
        clean_text(
            row.get(
                "availability",
                ""
            )
        ).lower()
    )


    # --------------------------------------------------------
    # PRICE SCORE
    # --------------------------------------------------------

    if price > 0:

        price_score = min(
            100,
            100000 / price
        )

    else:

        price_score = 0


    # --------------------------------------------------------
    # RATING SCORE
    # --------------------------------------------------------

    rating_score = (
        rating / 5
    ) * 100


    # --------------------------------------------------------
    # REVIEW SCORE
    # --------------------------------------------------------

    review_score = min(
        100,
        20
        +
        (
            min(
                reviews,
                10000
            )
            /
            10000
            *
            80
        )
    )


    # --------------------------------------------------------
    # AVAILABILITY SCORE
    # --------------------------------------------------------

    if (
        "out" in availability
        or
        "unavailable"
        in availability
    ):

        availability_score = 0

    else:

        availability_score = 100


    score = (
        price_score * 0.40
        +
        discount * 0.20
        +
        rating_score * 0.20
        +
        availability_score * 0.10
        +
        review_score * 0.10
    )


    return round(
        score,
        2
    )


# ============================================================
# CONVERT ROW TO PRODUCT DICTIONARY
# ============================================================

def product_dict(
    row
):

    price = safe_float(
        row.get(
            "price_inr",
            row.get(
                "price",
                0
            )
        )
    )

    mrp = safe_float(
        row.get(
            "mrp",
            0
        )
    )

    discount = safe_float(
        row.get(
            "discount",
            0
        )
    )

    rating = safe_float(
        row.get(
            "rating",
            0
        )
    )

    reviews = safe_int(
        row.get(
            "reviews",
            0
        )
    )

    marketplace = (
        clean_text(
            row.get(
                "marketplace",
                ""
            )
        ).lower()
    )


    return {

        "marketplace":
            MARKETPLACE_DISPLAY.get(
                marketplace,
                marketplace.title()
            ),

        "marketplace_key":
            marketplace,

        "product_id":
            clean_text(
                row.get(
                    "product_id",
                    ""
                )
            ),

        "product_name":
            clean_text(
                row.get(
                    "product_name",
                    ""
                )
            ),

        "brand":
            clean_text(
                row.get(
                    "brand",
                    ""
                )
            ),

        "category":
            clean_text(
                row.get(
                    "category",
                    ""
                )
            ),

        "price":
            round(
                price,
                2
            ),

        "price_inr":
            round(
                price,
                2
            ),

        "mrp":
            round(
                mrp,
                2
            ),

        "discount":
            round(
                discount,
                2
            ),

        "rating":
            round(
                rating,
                2
            ),

        "reviews":
            reviews,

        "availability":
            clean_text(
                row.get(
                    "availability",
                    ""
                )
            )
            or
            "Available",

        "image":
            get_display_image(row),

        "product_url":
            get_product_url(
                row.get(
                    "product_url",
                    ""
                )
            ),

        "deal_score":
            deal_score(
                row
            ),
    }


# ============================================================
# SEARCH SCORE
# ============================================================

def calculate_search_score(
    query,
    product_name,
    brand,
    category
):

    if fuzz is None:
        return 0

    query_normalized = (
        normalize_name(query)
    )

    product_normalized = (
        normalize_name(product_name)
    )

    if not query_normalized:
        return 0


    query_tokens = set(
        tokenize(
            query_normalized
        )
    )

    product_tokens = set(
        tokenize(
            product_normalized
        )
    )


    # Exact full-name match
    if (
        query_normalized
        ==
        product_normalized
    ):

        return 100


    # Query contained inside name
    if (
        query_normalized
        in
        product_normalized
    ):

        base = 96

    else:

        base = fuzz.token_set_ratio(
            query_normalized,
            product_normalized
        )


    # Token coverage
    common_tokens = (
        query_tokens
        &
        product_tokens
    )

    if query_tokens:

        coverage = (
            len(common_tokens)
            /
            len(query_tokens)
        ) * 100

    else:

        coverage = 0


    score = (
        base * 0.60
        +
        coverage * 0.40
    )


    # Brand support
    detected_brand = detect_brand(
        query
    )

    if detected_brand:

        product_brand = normalize_name(
            brand
        )

        if (
            detected_brand
            in product_normalized
            or
            detected_brand
            in product_brand
        ):

            score += 10


    # Category support
    category_text = normalize_name(
        category
    )

    if (
        any(
            token in category_text
            for token in query_tokens
        )
    ):

        score += 4


    return min(
        100,
        score
    )


# ============================================================
# SEARCH PRODUCTS
# ============================================================

def search_products(query="", marketplace="", max_results=60):
    """Search only real products; accessories/remotes are excluded before ranking."""
    if marketplace_df.empty:
        return []
    data = marketplace_df.copy()
    try:
        data = data[~data.apply(is_accessory_product, axis=1)].copy()
    except Exception:
        pass
    if marketplace:
        wanted = normalize_marketplace(marketplace)
        data = data[data["marketplace"].apply(normalize_marketplace).eq(wanted)]
    if data.empty:
        return []
    query = clean_text(query)
    if not query:
        data["_deal"] = data.apply(deal_score, axis=1)
        data = data.sort_values("_deal", ascending=False).head(max(1, int(max_results)))
        return [product_dict(row) for _, row in data.iterrows()]
    q = normalize_name(query)
    tokens = set(tokenize(q))
    candidates = []
    for _, row in data.iterrows():
        name = clean_text(row.get("product_name", ""))
        brand = clean_text(row.get("brand", ""))
        category = clean_text(row.get("category", ""))
        name_norm = normalize_name(name)
        nt = set(tokenize(name_norm))
        hay_tokens = set(tokenize(normalize_name(" ".join((name, brand, category)))))
        if not tokens.issubset(hay_tokens):
            continue
        nums = {t for t in tokens if re.search(r"\d", t)}
        if nums and not all(any(n in t for t in nt) for n in nums):
            continue
        score = 120 if q == name_norm else (100 if q in name_norm else calculate_search_score(query, name, brand, category))
        product = product_dict(row)
        product["match_score"] = round(score, 2)
        candidates.append(product)
    market_priority = {"flipkart": 0, "croma": 1, "amazon": 2, "bestbuy": 3}
    candidates.sort(key=lambda p: (market_priority.get(normalize_marketplace(p.get("marketplace_key", "")), 99), -p.get("match_score", 0), -p.get("deal_score", 0)))
    unique, seen = [], set()
    for product in candidates:
        key = (normalize_marketplace(product.get("marketplace_key", "")), str(product.get("product_id", "")), normalize_name(product.get("product_name", "")))
        if key in seen:
            continue
        seen.add(key); unique.append(product)
        if len(unique) >= max(1, int(max_results)):
            break
    return unique

# ============================================================
# MARKETPLACE SUMMARY
# ============================================================

def _marketplace_price_inr(data):
    """Return a usable INR average for a marketplace."""
    if data is None or data.empty:
        return 0.0
    values = pd.to_numeric(data.get("price_inr", pd.Series(dtype=float)), errors="coerce")
    source = pd.to_numeric(data.get("price", pd.Series(dtype=float)), errors="coerce")
    if values.notna().any() and (values > 0).any():
        return float(values[values > 0].mean())
    if source.notna().any() and (source > 0).any():
        avg = float(source[source > 0].mean())
        currencies = data.get("currency", pd.Series("", index=data.index)).astype(str).str.lower()
        if currencies.str.contains(r"usd|dollar|\$", regex=True).any():
            return avg * 85.0
        return avg
    return 0.0

def marketplace_summary():

    result = {}

    if marketplace_df.empty:
        return result


    for market in MARKETPLACES:

        data = marketplace_df[
            marketplace_df[
                "marketplace"
            ]
            ==
            market
        ]


        result[market] = {

            "products":
                int(
                    len(data)
                ),

            "rating":
                round(
                    float(
                        data[
                            "rating"
                        ].mean()
                    )
                    if len(data)
                    else 0,
                    2
                ),

            "discount":
                round(
                    float(
                        data[
                            "discount"
                        ].mean()
                    )
                    if len(data)
                    else 0,
                    2
                ),

            "price":
                round(
                    _marketplace_price_inr(data),
                    2
                ),
        }


    return result


# ============================================================
# TOP PRODUCTS
# ============================================================

def top_products(
    market,
    limit=5
):

    if marketplace_df.empty:
        return []


    data = marketplace_df[
        marketplace_df[
            "marketplace"
        ]
        ==
        market
    ].copy()


    if data.empty:
        return []


    data["deal_score_temp"] = (
        data.apply(
            deal_score,
            axis=1
        )
    )


    data = (
        data
        .sort_values(
            "deal_score_temp",
            ascending=False
        )
        .head(
            limit
        )
    )


    return [
        product_dict(row)
        for _, row
        in data.iterrows()
    ]


# ============================================================
# VERIFIED + OPTIONAL COMPARE
# ============================================================

@lru_cache(maxsize=1)
def compare_products():
    """Build cross-marketplace comparisons using category + product identity.

    The important rule here is that marketplace titles do NOT have to be an
    exact string match and the full model number is NOT required.  A match is
    primarily based on:
      1. same marketplace-normalized brand,
      2. same product category/type,
      3. strong overlap of meaningful product words.

    Model numbers are only a bonus when available.  This allows the same TV,
    phone, laptop, etc. to match even when Amazon/Flipkart/Croma/Best Buy use
    different title formats, while the category check prevents a brand's TV
    from being matched with its earbuds or another unrelated product.
    """
    if marketplace_df.empty or "marketplace" not in marketplace_df.columns:
        return []

    data = marketplace_df.copy()
    try:
        data = data[~data.apply(is_accessory_product, axis=1)].copy()
    except Exception:
        pass
    if data.empty:
        return []

    data["_market"] = data["marketplace"].astype(str).map(normalize_marketplace)
    data = data[data["_market"].isin(MARKETPLACES)].copy()
    if data.empty:
        return []

    large_types = {
        "tv", "phone", "tablet", "laptop", "watch", "refrigerator",
        "washing_machine", "ac", "microwave", "camera", "monitor",
        "printer", "speaker", "headphones", "earbuds", "gaming_console"
    }

    preferred_brands = {
        "apple", "samsung", "xiaomi", "oneplus", "vivo", "oppo",
        "realme", "motorola", "google", "pixel", "tcl", "lg", "sony",
        "hisense", "panasonic", "philips", "bosch", "whirlpool", "haier",
        "lenovo", "hp", "dell", "asus", "acer", "microsoft", "canon",
        "nikon", "boat", "jbl", "bose", "noise", "fitbit", "garmin"
    }

    PRODUCT_TYPES = {
        "tv": {"tv", "television", "smarttv", "ledtv", "oled", "qled", "miniled"},
        "phone": {"phone", "smartphone", "mobile", "iphone", "galaxy", "pixel"},
        "tablet": {"tablet", "ipad"},
        "laptop": {"laptop", "notebook", "macbook", "chromebook", "ultrabook"},
        "watch": {"watch", "smartwatch", "fitnessband", "band"},
        "headphones": {"headphones", "headphone", "overear", "onear", "headset"},
        "earbuds": {"earbuds", "earbud", "buds", "tws", "airpods"},
        "speaker": {"speaker", "soundbar", "subwoofer"},
        "camera": {"camera", "dslr", "mirrorless", "camcorder"},
        "refrigerator": {"refrigerator", "fridge"},
        "washing_machine": {"washing", "washer", "washingmachine"},
        "ac": {"ac", "airconditioner", "splitac", "aircondition"},
        "microwave": {"microwave", "oven", "microwaveoven"},
        "printer": {"printer", "multifunctionprinter"},
        "monitor": {"monitor", "display"},
        "gaming_console": {"playstation", "xbox", "nintendo", "console"},
    }

    # Generic words that describe a specification rather than product identity.
    # They are deliberately removed before comparing titles so that
    # "Samsung 43 inch 4K Smart TV Black" and a differently formatted title
    # can still be recognized as the same product family.
    SPEC_WORDS = {
        "smart", "led", "oled", "qled", "mini", "inch", "inches", "series",
        "model", "new", "latest", "black", "white", "silver", "blue", "grey",
        "gray", "gold", "red", "green", "5g", "4g", "wifi", "wi-fi", "bluetooth",
        "dual", "sim", "unlocked", "international", "global", "edition", "2021",
        "2022", "2023", "2024", "2025", "2026", "2027", "gb", "tb", "mb",
        "ram", "rom", "storage", "memory", "full", "hd", "fhd", "uhd", "4k",
        "8k", "hdr", "pro", "max", "plus", "ultra", "lite", "prime", "air",
        "gen", "generation", "ton", "tons", "kg", "w", "watts", "hz", "mp",
        "mah", "mah", "star", "rating", "voice", "assistant", "with", "the",
        "for", "and", "of", "on", "from", "new", "latest", "smartphone"
    }

    def product_type(name, row=None):
        text = normalize_name(clean_text(name))
        tokens = set(tokenize(text))
        category_text = ""
        if row is not None:
            category_text = normalize_name(clean_text(row.get("category", "")))
            tokens |= set(tokenize(category_text))
        # Longer/more specific categories first.
        for kind, words in PRODUCT_TYPES.items():
            if tokens.intersection(words):
                return kind
        return ""

    def get_brand(name, row=None):
        b = ""
        if row is not None:
            b = normalize_name(clean_text(row.get("brand", "")))
        if not b:
            b = normalize_name(detect_brand(name) or "")
        return BRAND_ALIASES.get(b, b)

    def model_tokens(name):
        return set(extract_model_tokens(name))

    def identity_tokens(name):
        """Return useful product words, not the full title/model string."""
        tokens = []
        for token in tokenize(name):
            t = normalize_name(token)
            if not t or t in SPEC_WORDS:
                continue
            # Drop pure numbers and measurement/spec fragments.
            if t.isdigit():
                continue
            if re.fullmatch(r"\d+(?:gb|tb|mb|kg|w|hz|mp|mah)", t):
                continue
            # Model-like alphanumeric codes are useful as a bonus, but not
            # essential for a cross-marketplace match.
            if len(t) <= 1:
                continue
            tokens.append(t)
        return set(tokens)

    def prepare(frame):
        records = []
        for idx, row in frame.iterrows():
            name = normalize_name(clean_text(row.get("product_name", "")))
            if not name:
                continue
            brand = get_brand(name, row)
            typ = product_type(name, row)
            if brand == "nokia":
                continue
            # Unknown categories are kept only for strong preferred brands;
            # known consumer-product categories are always eligible.
            if typ not in large_types and brand not in preferred_brands:
                continue
            records.append({
                "idx": idx,
                "row": row,
                "name": name,
                "brand": brand,
                "type": typ,
                "models": model_tokens(name),
                "identity": identity_tokens(name),
            })
        return records

    pools = {}
    for market in MARKETPLACES:
        pools[market] = prepare(data[data["_market"] == market])

    if not any(pools.values()):
        return []

    def compatible(base, cand):
        # Brand and category are the hard gates. This is the key change from
        # the previous version: the complete title/model is NOT the gate.
        if base["brand"] and cand["brand"] and base["brand"] != cand["brand"]:
            return False
        if base["type"] and cand["type"] and base["type"] != cand["type"]:
            return False
        # If one side has a known category and the other side has no category,
        # do not allow a weak fuzzy match to cross product types.
        if base["type"] and not cand["type"]:
            return False
        if cand["type"] and not base["type"]:
            return False
        return True

    def score(base, cand):
        if not compatible(base, cand):
            return -1

        a = base["identity"]
        b = cand["identity"]
        common = a.intersection(b)
        union = a.union(b)
        overlap = (len(common) / max(1, min(len(a), len(b)))) * 100
        jaccard = (len(common) / max(1, len(union))) * 100
        text_score = fuzz.token_set_ratio(base["name"], cand["name"]) if fuzz else 0

        # Same model code is a strong bonus, not a requirement.
        model_common = base["models"].intersection(cand["models"])
        model_bonus = 18 if model_common else 0

        # Product identity is more important than the raw title string.
        value = (overlap * 0.45) + (jaccard * 0.25) + (text_score * 0.30) + model_bonus
        if base["type"] and cand["type"] and base["type"] == cand["type"]:
            value += 12
        if base["brand"] and cand["brand"] and base["brand"] == cand["brand"]:
            value += 10
        return value

    def find_best(base, market):
        rows = pools.get(market, [])
        if not rows:
            return None

        narrowed = [r for r in rows if compatible(base, r)]
        if not narrowed:
            return None

        # RapidFuzz is used only to shortlist candidates; the final decision
        # comes from category + brand + meaningful identity-token scoring.
        if fuzz and process:
            choices = {r["name"]: i for i, r in enumerate(narrowed)}
            hits = process.extract(
                base["name"],
                choices.keys(),
                scorer=fuzz.token_set_ratio,
                limit=min(15, len(choices))
            )
            candidate_rows = [narrowed[choices[name]] for name, _, _ in hits]
        else:
            candidate_rows = narrowed[:25]

        best = None
        best_score = -1
        for cand in candidate_rows:
            sc = score(base, cand)
            if sc > best_score:
                best_score = sc
                best = cand

        if best is None:
            return None

        # A model overlap can pass comfortably. Without a model overlap, the
        # product identity still needs meaningful agreement; category/brand
        # alone is not enough because Samsung has many different TVs/phones.
        common_models = base["models"].intersection(best["models"])
        common_identity = base["identity"].intersection(best["identity"])
        min_identity = min(len(base["identity"]), len(best["identity"]))

        if common_models and best_score >= 85:
            return best
        if min_identity <= 1:
            return best if best_score >= 91 else None
        if len(common_identity) >= 2 and best_score >= 78:
            return best
        if len(common_identity) >= 1 and best_score >= 88:
            return best
        return None

    raw_results = []
    for base_market in MARKETPLACES:
        for base in pools.get(base_market, []):
            matches = {base_market: base["row"]}
            for market in MARKETPLACES:
                if market == base_market:
                    continue
                found = find_best(base, market)
                if found is not None:
                    matches[market] = found["row"]

            if len(matches) < 2:
                continue

            # Prefer the most descriptive marketplace title as the display name.
            rep = max(
                matches.values(),
                key=lambda r: len(clean_text(r.get("product_name", "")))
            )
            rep_product = product_dict(rep)
            raw_results.append({
                "product_name": rep_product.get("product_name", ""),
                "amazon": product_dict(matches["amazon"]) if "amazon" in matches else None,
                "flipkart": product_dict(matches["flipkart"]) if "flipkart" in matches else None,
                "croma": product_dict(matches["croma"]) if "croma" in matches else None,
                "bestbuy": product_dict(matches["bestbuy"]) if "bestbuy" in matches else None,
                "_brand": get_brand(rep_product.get("product_name", ""), rep),
                "_type": product_type(rep_product.get("product_name", ""), rep),
                "_models": model_tokens(rep_product.get("product_name", "")),
                "_identity": identity_tokens(rep_product.get("product_name", "")),
            })

    # De-duplicate overlapping anchor results. Use category + brand + the
    # meaningful product identity, not the entire title/model string.
    unique = {}
    for item in raw_results:
        identity = item.get("_identity", set())
        brand = item.get("_brand", "")
        typ = item.get("_type", "")
        if identity:
            key = (brand, typ, tuple(sorted(identity)))
        else:
            key = (brand, typ, normalize_name(item.get("product_name", "")))

        existing = unique.get(key)
        if existing is None:
            unique[key] = item
        else:
            old_count = sum(existing.get(m) is not None for m in MARKETPLACES)
            new_count = sum(item.get(m) is not None for m in MARKETPLACES)
            if new_count > old_count:
                unique[key] = item

    results = list(unique.values())
    results.sort(key=lambda x: (
        -sum(x.get(m) is not None for m in MARKETPLACES),
        0 if x.get("_type") in {"tv", "phone", "laptop", "tablet"} else 1,
        0 if x.get("_brand") in preferred_brands else 1,
        x.get("product_name", ""),
    ))

    for item in results:
        item.pop("_brand", None)
        item.pop("_type", None)
        item.pop("_models", None)
        item.pop("_identity", None)
    return results


# ============================================================
# IMAGE PROXY
# ============================================================

@app.route("/image-proxy")
def image_proxy():
    image_url = request.args.get("url", "").strip()
    if image_url.startswith("/static/croma_images/"):
        return redirect(image_url)

    if not image_url:
        return Response("Missing image URL", status=400)

    # Do not use unquote() here.
    # Flask already decodes the query parameter.

    from urllib.parse import urlparse

    parsed = urlparse(image_url)

    allowed_hosts = {
        "media.croma.com",
        "m.media-amazon.com",
        "images-na.ssl-images-amazon.com",
        "img.bbystatic.com",
        "rukminim1.flixcart.com",
        "rukminim2.flixcart.com",
        "rukminim3.flixcart.com",
        "rukminim4.flixcart.com",
    }

    if parsed.scheme != "https" or parsed.hostname not in allowed_hosts:
        return Response("Invalid image URL", status=400)

    # Use the appropriate referrer for each image source.
    if parsed.hostname == "media.croma.com":
        referer = "https://www.croma.com/"
    elif "amazon" in parsed.hostname:
        referer = "https://www.amazon.com/"
    elif "bbystatic" in parsed.hostname:
        referer = "https://www.bestbuy.com/"
    else:
        referer = "https://www.flipkart.com/"

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/131.0.0.0 Safari/537.36"
        ),
        "Accept": "image/avif,image/webp,image/apng,image/*,*/*;q=0.8",
        "Referer": referer,
    }

    if parsed.hostname == "media.croma.com":
        headers["Origin"] = "https://www.croma.com"

    try:
        response = requests.get(
            image_url,
            headers=headers,
            timeout=15,
            stream=True,
        )

        if response.status_code != 200:
            print("Image URL:", image_url)
            print("Upstream status:", response.status_code)

            return Response(
                f"Image source returned HTTP {response.status_code}",
                status=502,
                content_type="text/plain",
                headers={
                    "X-Upstream-Status": str(response.status_code)
                },
            )

        content_type = response.headers.get("Content-Type", "")

        if not content_type.startswith("image/"):
            print("Invalid image content type:", content_type)
            return Response("Invalid image response", status=502)

        return Response(
            response.content,
            status=200,
            content_type=content_type,
            headers={
                "Cache-Control": "public, max-age=86400"
            },
        )

    except requests.RequestException as e:
        print("Image proxy error:", str(e))
        print("Image URL:", image_url)

        return Response(
            "Image server unavailable",
            status=502,
            content_type="text/plain",
        )


# ============================================================
# HOME
# ============================================================

@app.route("/")
def home():

    return render_template(
        "home.html"
    )


# ============================================================
# REGISTER
# ============================================================

@app.route(
    "/register",
    methods=[
        "GET",
        "POST"
    ]
)
def register():

    if request.method == "POST":

        username = request.form.get(
            "username",
            ""
        ).strip()

        email = request.form.get(
            "email",
            ""
        ).strip()

        password = request.form.get(
            "password",
            ""
        )


        if not username:
            return "Username is required."


        if not email:
            return "Email is required."


        if not password:
            return "Password is required."


        conn = db()

        cursor = conn.cursor()


        try:

            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT,
                    email TEXT UNIQUE,
                    password TEXT
                )
                """
            )


            cursor.execute(
                """
                INSERT INTO users (
                    username,
                    email,
                    password
                )
                VALUES (?, ?, ?)
                """,
                (
                    username,
                    email,
                    password
                )
            )


            conn.commit()


        except sqlite3.IntegrityError:

            conn.close()

            return (
                "Email already registered. "
                "Please login."
            )


        finally:

            try:
                conn.close()
            except Exception:
                pass


        return redirect(
            "/login"
        )


    return render_template(
        "register.html"
    )


# ============================================================
# LOGIN
# ============================================================

@app.route(
    "/login",
    methods=[
        "GET",
        "POST"
    ]
)
def login():

    if request.method == "POST":

        email = request.form.get(
            "email",
            ""
        ).strip()

        password = request.form.get(
            "password",
            ""
        )


        conn = db()

        cursor = conn.cursor()


        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT,
                email TEXT UNIQUE,
                password TEXT
            )
            """
        )


        conn.commit()


        cursor.execute(
            """
            SELECT *
            FROM users
            WHERE email=?
            AND password=?
            """,
            (
                email,
                password
            )
        )


        user = cursor.fetchone()

        conn.close()


        if user:

            session[
                "username"
            ] = user[
                "username"
            ]

            return redirect(
                "/dashboard"
            )


        return (
            "Invalid Email or Password"
        )


    return render_template(
        "login.html"
    )


# ============================================================
# LOGOUT
# ============================================================

@app.route(
    "/logout"
)
def logout():

    session.clear()

    return redirect(
        "/"
    )


# ============================================================
# DASHBOARD
# ============================================================

@app.route(
    "/dashboard"
)
def dashboard():

    if "username" not in session:

        return redirect(
            "/login"
        )


    summary = (
        marketplace_summary()
    )


    return render_template(

        "dashboard.html",

        username=
            session[
                "username"
            ],

        amazon_products=
            summary.get(
                "amazon",
                {}
            ).get(
                "products",
                0
            ),

        flipkart_products=
            summary.get(
                "flipkart",
                {}
            ).get(
                "products",
                0
            ),

        croma_products=
            summary.get(
                "croma",
                {}
            ).get(
                "products",
                0
            ),

        bestbuy_products=
            summary.get(
                "bestbuy",
                {}
            ).get(
                "products",
                0
            ),

        amazon_top=
            top_products(
                "amazon",
                4
            ),

        flipkart_top=
            top_products(
                "flipkart",
                4
            ),

        croma_top=
            top_products(
                "croma",
                4
            ),

        bestbuy_top=
            top_products(
                "bestbuy",
                4
            ),

        marketplace_summary=
            summary,
    )


# ============================================================
# MARKETPLACE SUMMARY API
# ============================================================

@app.route(
    "/api/marketplace-summary"
)
def summary_api():

    if "username" not in session:

        return jsonify(
            {
                "error":
                    "Unauthorized"
            }
        ), 401


    summary = (
        marketplace_summary()
    )


    return jsonify({

        "Amazon":
            summary.get(
                "amazon",
                {}
            ).get(
                "products",
                0
            ),

        "Flipkart":
            summary.get(
                "flipkart",
                {}
            ).get(
                "products",
                0
            ),

        "Croma":
            summary.get(
                "croma",
                {}
            ).get(
                "products",
                0
            ),

        "Best Buy":
            summary.get(
                "bestbuy",
                {}
            ).get(
                "products",
                0
            ),
    })


# ============================================================
# SEARCH
# ============================================================

@app.route(
    "/search",
    methods=[
        "GET",
        "POST"
    ]
)
def search():

    if "username" not in session:

        return redirect(
            "/login"
        )


    # --------------------------------------------------------
    # GET OR POST QUERY
    # --------------------------------------------------------

    if request.method == "POST":

        query = request.form.get(
            "keyword",
            request.form.get(
                "q",
                ""
            )
        ).strip()

        marketplace = request.form.get(
            "marketplace",
            ""
        ).strip()

    else:

        query = request.args.get(
            "q",
            request.args.get(
                "keyword",
                ""
            )
        ).strip()

        marketplace = request.args.get(
            "marketplace",
            ""
        ).strip()


    # --------------------------------------------------------
    # NORMALIZE MARKETPLACE
    # --------------------------------------------------------

    if marketplace:

        marketplace = normalize_name(
            marketplace
        )


        if marketplace not in MARKETPLACES:

            marketplace = ""


    # --------------------------------------------------------
    # SEARCH
    # --------------------------------------------------------

    results = search_products(
        query,
        marketplace,
        60
    )


    # --------------------------------------------------------
    # IMPORTANT:
    # lowest_price MUST BE A PRODUCT DICTIONARY,
    # NOT A FLOAT.
    #
    # This fixes:
    # 'float object has no attribute price'
    # --------------------------------------------------------

    lowest_price = None

    valid_price_results = [
        product
        for product in results
        if safe_float(
            product.get(
                "price",
                0
            )
        ) > 0
    ]


    if valid_price_results:

        lowest_price = min(
            valid_price_results,
            key=lambda product:
                safe_float(
                    product.get(
                        "price",
                        0
                    )
                )
        )


    # --------------------------------------------------------
    # BEST DEAL
    # --------------------------------------------------------

    best_deal = None


    if results:

        best_deal = max(
            results,
            key=lambda product:
                safe_float(
                    product.get(
                        "deal_score",
                        0
                    )
                )
        )


    # --------------------------------------------------------
    # SORT OPTION
    # --------------------------------------------------------

    sort_option = request.args.get(
        "sort",
        ""
    ).strip().lower()


    if sort_option == "price":

        results.sort(
            key=lambda product:
                safe_float(
                    product.get(
                        "price",
                        0
                    )
                )
            if safe_float(
                product.get(
                    "price",
                    0
                )
            ) > 0
            else float("inf")
        )


    elif sort_option == "deal":

        results.sort(
            key=lambda product:
                safe_float(
                    product.get(
                        "deal_score",
                        0
                    )
                ),
            reverse=True
        )


    elif sort_option == "rating":

        results.sort(
            key=lambda product:
                safe_float(
                    product.get(
                        "rating",
                        0
                    )
                ),
            reverse=True
        )


    elif sort_option == "discount":

        results.sort(
            key=lambda product:
                safe_float(
                    product.get(
                        "discount",
                        0
                    )
                ),
            reverse=True
        )


    return render_template(

        "search.html",

        # Main result list
        results=results,

        products=results,

        result_count=len(
            results
        ),

        # Search text
        query=query,

        search_query=query,

        # Marketplace
        marketplace=marketplace,

        selected_marketplace=
            marketplace,

        marketplaces=[
            "Amazon",
            "Flipkart",
            "Croma",
            "Best Buy"
        ],

        # Sort
        selected_sort=
            sort_option,

        # IMPORTANT:
        # dictionaries, not numbers
        lowest_price=
            lowest_price,

        best_deal=
            best_deal,

        # Also provide numeric values
        # for templates that use them.
        lowest_price_value=
            (
                lowest_price[
                    "price"
                ]
                if lowest_price
                else None
            ),

        best_deal_score=
            (
                best_deal[
                    "deal_score"
                ]
                if best_deal
                else None
            ),
    )


# ============================================================
# PRODUCT DETAIL
# ============================================================

@app.route(
    "/product/<path:product_id>"
)
def product_detail(
    product_id
):

    if "username" not in session:

        return redirect(
            "/login"
        )


    if marketplace_df.empty:

        return render_template(
            "product.html",
            product=None,
            similar_products=[]
        )


    matches = marketplace_df[
        marketplace_df[
            "product_id"
        ].astype(str)
        ==
        str(product_id)
    ]


    if matches.empty:

        matches = marketplace_df[
            marketplace_df[
                "normalized_name"
            ]
            ==
            normalize_name(
                product_id
            )
        ]


    if matches.empty:

        return render_template(
            "product.html",
            product=None,
            similar_products=[]
        )


    product = product_dict(
        matches.iloc[0]
    )


    similar_products = (
        search_products(
            product[
                "product_name"
            ],
            product[
                "marketplace_key"
            ],
            8
        )
    )


    return render_template(

        "product.html",

        product=product,

        similar_products=
            similar_products,
    )


# ============================================================
# COMPARE
# ============================================================


@app.route("/compare", methods=["GET", "POST"])
def compare():
    # Category + brand comparison. No individual product/model selector.
    if "username" not in session:
        return redirect("/login")

    data = marketplace_df.copy()
    if data.empty:
        return Response("No marketplace data available.", status=200)
    try:
        data = data[~data.apply(is_accessory_product, axis=1)].copy()
    except Exception:
        pass
    data["_market"] = data["marketplace"].apply(normalize_marketplace)
    data = data[data["_market"].isin(MARKETPLACES)].copy()

    category_map = {
        "tv":"TVs", "phone":"Mobiles", "tablet":"Tablets", "laptop":"Laptops",
        "watch":"Smart Watches", "earbuds":"Earphones / Earbuds", "headphones":"Headphones",
        "speaker":"Speakers", "camera":"Cameras", "refrigerator":"Refrigerators",
        "washing_machine":"Washing Machines", "ac":"Air Conditioners", "microwave":"Microwaves",
        "printer":"Printers", "monitor":"Monitors", "gaming_console":"Gaming Consoles",
    }
    type_words = {
        "tv":{"tv","television","smarttv","ledtv","oled","qled","miniled"},
        "phone":{"phone","smartphone","mobile","iphone","galaxy","pixel"},
        "tablet":{"tablet","ipad"}, "laptop":{"laptop","notebook","macbook","chromebook","ultrabook"},
        "watch":{"watch","smartwatch","fitnessband","band"},
        "earbuds":{"earbuds","earbud","buds","tws","airpods"},
        "headphones":{"headphones","headphone","headset","overear","onear"},
        "speaker":{"speaker","soundbar","subwoofer"}, "camera":{"camera","dslr","mirrorless","camcorder"},
        "refrigerator":{"refrigerator","fridge"}, "washing_machine":{"washing","washer","washingmachine"},
        "ac":{"airconditioner","splitac","aircondition","ac"}, "microwave":{"microwave","oven","microwaveoven"},
        "printer":{"printer","multifunctionprinter"}, "monitor":{"monitor","display"},
        "gaming_console":{"playstation","xbox","nintendo","console"},
    }

    def get_type(row):
        s=normalize_name(f"{row.get('product_name','')} {row.get('category','')}")
        tokens=set(tokenize(s))
        for kind, words in type_words.items():
            if tokens.intersection(words): return kind
        if "washing machine" in s or "washer" in s: return "washing_machine"
        if "air conditioner" in s or "split ac" in s: return "ac"
        if "smart tv" in s or "television" in s: return "tv"
        if "smartphone" in s or "mobile phone" in s: return "phone"
        return ""

    def get_brand(row):
        raw=normalize_name(row.get("brand",""))
        name=normalize_name(row.get("product_name",""))
        if raw:
            if raw in BRAND_ALIASES: return BRAND_ALIASES[raw]
            for token in raw.split():
                if token in BRAND_ALIASES: return BRAND_ALIASES[token]
            return raw
        return detect_brand(name) or ""

    prepared=[]
    for _, row in data.iterrows():
        kind=get_type(row); brand=get_brand(row)
        if not kind or not brand: continue
        if kind=="phone" and brand=="nokia": continue
        prepared.append((kind,brand,row))

    category=request.values.get("category","").strip()
    brand=request.values.get("brand","").strip()

    # Only offer categories/brands that actually have products on at least
    # 2 marketplaces. This keeps the dropdown useful and prevents random
    # one-store brands from appearing. The coverage is calculated from the
    # current dataset, so TV brands are shown under TVs, mobile brands under
    # Mobiles, earbud brands under Earphones, etc.
    coverage = {}
    for k, b, row in prepared:
        market = normalize_marketplace(row.get("_market", ""))
        if market not in MARKETPLACES:
            continue
        coverage.setdefault((k, b), set()).add(market)

    available_categories=sorted(
        {k for (k, b), markets in coverage.items() if len(markets) >= 2},
        key=lambda x:list(category_map).index(x) if x in category_map else 99
    )

    available_brands=sorted(
        {b for (k, b), markets in coverage.items()
         if len(markets) >= 2 and (not category or k == category)}
    )

    # If a previously selected brand is not valid for the selected category,
    # do not show its products.
    if category and brand and len(coverage.get((category, brand), set())) < 2:
        brand = ""

    # Once category + brand are selected, show ALL products for that brand,
    # grouped into one row per marketplace. Do not try to match model names.
    selected=[row for k,b,row in prepared if category and brand and k==category and b==brand]
    marketplace_products={m:[] for m in MARKETPLACES}
    for row in selected:
        m=normalize_marketplace(row.get("_market",""))
        if m in marketplace_products: marketplace_products[m].append(row)

    for m, rows in marketplace_products.items():
        seen=set(); unique=[]
        for row in rows:
            name=clean_text(row.get("product_name","")); price=safe_float(row.get("price",0))
            key=(normalize_name(name),round(price,2) if price else 0)
            if key in seen: continue
            seen.add(key); unique.append(row)
        unique.sort(key=lambda r:(safe_float(r.get("price",0))<=0,safe_float(r.get("price",0)) or 999999999,clean_text(r.get("product_name","")).lower()))
        marketplace_products[m]=unique

    best_price=None; best_market=None; best_product=None
    for m in MARKETPLACES:
        for row in marketplace_products[m]:
            price=safe_float(row.get("price",0))
            if price>0 and (best_price is None or price<best_price):
                best_price=price; best_market=MARKETPLACE_DISPLAY.get(m,m.title()); best_product=clean_text(row.get("product_name",""))

    def esc(v):
        return str(v or "").replace("&","&amp;").replace("<","&lt;").replace(">","&gt;").replace('"',"&quot;").replace("'","&#39;")
    cat_options="".join(f'<option value="{esc(k)}" {"selected" if k==category else ""}>{esc(category_map.get(k,k.title()))}</option>' for k in available_categories)
    brand_options="".join(f'<option value="{esc(b)}" {"selected" if b==brand else ""}>{esc(b.title())}</option>' for b in available_brands)

    marketplace_rows=""; found=0; total=0
    market_classes={"amazon":"amazon","flipkart":"flipkart","croma":"croma","bestbuy":"bestbuy"}
    for m in MARKETPLACES:
        rows=marketplace_products[m]; display=MARKETPLACE_DISPLAY.get(m,m.title())
        cls=market_classes.get(m,m)
        if rows:
            found+=1; total+=len(rows); lines=[]
            for row in rows:
                name=clean_text(row.get("product_name","")) or "Unnamed product"
                price=safe_float(row.get("price",0)); ptxt=f"₹{price:,.0f}" if price>0 else "Price unavailable"
                lines.append(f'<div class="product-line"><span class="product-name">{esc(name)}</span><span class="product-price">{ptxt}</span></div>')
            marketplace_rows+=f'<tr class="market-row {cls}"><td class="market-name"><span class="market-badge"><span class="market-dot"></span>{esc(display)}</span><span class="market-count">{len(rows)} products</span></td><td><div class="product-list">{"".join(lines)}</div></td></tr>'
        else:
            marketplace_rows+=f'<tr class="market-row {cls} muted-row"><td class="market-name"><span class="market-badge"><span class="market-dot"></span>{esc(display)}</span><span class="market-count">0 products</span></td><td class="not-found">No products found for this brand</td></tr>'


    if category and brand and total:
        summary=f'<div class="summary"><b>{found} of 4 marketplaces found</b> &nbsp; | &nbsp; <b>{total} products shown</b></div>'
        if best_price is not None:
            summary+=f'<div class="best-box"><b>Best Price: ₹{best_price:,.0f}</b> — {esc(best_market)}<div class="best-product">{esc(best_product)}</div></div>'
        result=f'<h2>{esc(category_map.get(category,category.title()))} — {esc(brand.title())}</h2><table><thead><tr><th style="width:180px">Marketplace</th><th>All products and prices</th></tr></thead><tbody>{marketplace_rows}</tbody></table>'
    elif category and brand:
        summary='<div class="empty">No products found for this category and brand.</div>'; result=""
    else:
        summary='<div class="empty"><b>Select Category and Brand</b><br>Example: Mobiles → Apple. All Apple mobile products available in Amazon, Flipkart, Croma and Best Buy will be shown marketplace-wise. Images are not displayed.</div>'; result=""

    html=f'''<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Compare Products</title><style>
*{{box-sizing:border-box}}body{{font-family:Inter,Segoe UI,Arial,sans-serif;background:linear-gradient(135deg,#dff3ff 0%,#f4e7ff 35%,#fff1df 68%,#ddfff2 100%);margin:0;color:#172033}}.wrap{{max-width:1240px;margin:28px auto;padding:18px}}.box{{background:rgba(255,255,255,.97);border:1px solid #e5eaf3;border-radius:24px;padding:28px;box-shadow:0 18px 55px rgba(39,62,110,.13)}}.hero{{background:linear-gradient(135deg,#174ea6,#6c43c5 55%,#0e9f78);border-radius:20px;padding:25px;color:white;margin-bottom:24px;position:relative;overflow:hidden}}.hero:after{{content:"";position:absolute;width:180px;height:180px;border-radius:50%;right:-55px;top:-80px;background:rgba(255,255,255,.13)}}h1{{margin:0 0 7px;font-size:30px;position:relative;z-index:1}}.hero p{{margin:0;opacity:.9;line-height:1.55;position:relative;z-index:1}}.hint{{color:#667085;line-height:1.55;margin:0 0 20px}}.filters{{display:grid;grid-template-columns:1fr 1fr;gap:18px;background:linear-gradient(135deg,#eef7ff,#f8efff,#effff8);border:2px solid #d9d2ff;padding:18px;border-radius:18px}}.field{{position:relative}}label{{font-weight:700;display:block;margin-bottom:8px;color:#263653}}select,button{{width:100%;padding:14px 15px;border-radius:12px;border:1px solid #cfd7e6;box-sizing:border-box;background:white;font-size:15px;outline:none;transition:.2s}}select:hover,select:focus{{border-color:#6b5bd5;box-shadow:0 0 0 4px rgba(107,91,213,.10)}}button{{margin-top:16px;background:linear-gradient(90deg,#165bb0,#7148c9);color:white;font-weight:800;border:0;cursor:pointer;box-shadow:0 8px 20px rgba(57,76,170,.22);transition:transform .18s,box-shadow .18s}}button:hover{{transform:translateY(-2px);box-shadow:0 12px 26px rgba(57,76,170,.28)}}button:active{{transform:translateY(0)}}.summary{{display:flex;align-items:center;gap:10px;flex-wrap:wrap;margin:24px 0 12px;padding:15px 18px;border-radius:14px;background:linear-gradient(90deg,#dff1ff,#efe5ff,#e3fff2);color:#174b8f;border:1px solid #c9d9ff}}.best-box{{padding:18px 20px;margin:12px 0 22px;border-radius:16px;background:linear-gradient(135deg,#d9ffe9,#effff7,#fff9dc);border:2px solid #9fe2bd;color:#087a43;font-size:20px;box-shadow:0 8px 22px rgba(12,120,70,.08)}}.best-product{{margin-top:7px;font-size:13px;color:#475467;font-weight:normal;line-height:1.45}}.result-title{{display:flex;align-items:center;justify-content:space-between;gap:12px;flex-wrap:wrap;margin:25px 0 10px}}.result-title h2{{margin:0;font-size:24px;color:#182b49}}.table-wrap{{overflow-x:auto;border:1px solid #e3e8f2;border-radius:17px;background:#fff}}table{{width:100%;border-collapse:separate;border-spacing:0;margin:0;background:#fff;border:2px solid #d7ddf0;border-radius:17px;overflow:hidden;box-shadow:0 12px 30px rgba(69,55,130,.10)}}th,td{{padding:16px;border-bottom:1px solid #e8ecf3;text-align:left;vertical-align:top}}th{{background:linear-gradient(90deg,#dbeafe,#ede9fe,#dcfce7);color:#243b64;font-size:13px;text-transform:uppercase;letter-spacing:.04em}}tbody tr:last-child td{{border-bottom:0}}.market-row{{transition:transform .18s,box-shadow .18s,background .18s}}.market-row:nth-child(1) td{{background:linear-gradient(90deg,#fff7e6,#fffdf7)}}.market-row:nth-child(2) td{{background:linear-gradient(90deg,#eef5ff,#f9fbff)}}.market-row:nth-child(3) td{{background:linear-gradient(90deg,#fff0f1,#fffafa)}}.market-row:nth-child(4) td{{background:linear-gradient(90deg,#eef5ff,#f5f9ff)}}.market-row:hover td{{filter:brightness(.985);box-shadow:inset 0 0 0 999px rgba(255,255,255,.08)}}.market-name{{font-size:15px;white-space:nowrap;min-width:190px}}.market-badge{{display:inline-flex;align-items:center;gap:8px;font-weight:800;padding:8px 11px;border-radius:999px;background:#f3f6fb}}.market-dot{{width:9px;height:9px;border-radius:50%;display:inline-block}}.amazon .market-dot{{background:#ff9900}}.flipkart .market-dot{{background:#2874f0}}.croma .market-dot{{background:#e31b23}}.bestbuy .market-dot{{background:#0046be}}.amazon .market-badge{{background:#fff0cc;color:#9a5700;border:1px solid #ffd47a}}.flipkart .market-badge{{background:#e9f1ff;color:#1652a8;border:1px solid #bcd2ff}}.croma .market-badge{{background:#ffe9eb;color:#b4141b;border:1px solid #ffc1c6}}.bestbuy .market-badge{{background:#e8f0ff;color:#003b9a;border:1px solid #bfd2ff}}.market-count{{display:block;font-size:12px;color:#8a94a6;margin:7px 0 0 4px}}.product-list{{display:flex;flex-direction:column;gap:8px}}.product-line{{display:flex;justify-content:space-between;align-items:flex-start;gap:25px;padding:12px 13px;border:1px solid #edf0f5;border-radius:11px;background:linear-gradient(135deg,#ffffff,#f7f9ff);transition:.18s}}.product-line:hover{{background:#f5f8ff;border-color:#d9e2f4;transform:translateX(3px)}}.product-name{{line-height:1.45;color:#153f78;font-size:14px}}.product-price{{font-weight:900;white-space:nowrap;color:#111827;background:linear-gradient(135deg,#dcfce7,#ecfdf5);color:#087a43;border:1px solid #a7e8c2;padding:6px 10px;border-radius:9px}}.not-found{{color:#98a2b3;padding-top:10px}}.muted-row{{opacity:.72}}.empty{{padding:28px;margin-top:20px;color:#667085;background:linear-gradient(135deg,#f8fafc,#f5f2ff);border:1px dashed #cfd7e6;border-radius:16px;text-align:center;line-height:1.6}}.tip{{margin-top:15px;font-size:12px;color:#7a8495;text-align:center}}@media(max-width:800px){{.wrap{{padding:10px;margin:10px auto}}.box{{padding:16px;border-radius:18px}}.hero{{padding:20px}}h1{{font-size:25px}}.filters{{grid-template-columns:1fr}}.product-line{{flex-direction:column;gap:8px}}.market-name{{white-space:normal;min-width:140px}}}}
</style></head><body><div class="wrap"><div class="box"><div class="hero"><h1>🛍️ Smart Product Comparison</h1><p>Choose a category and brand to see every matching product marketplace-wise and find the lowest price.</p></div><p class="hint">Only <b>Category → Brand</b> is needed. For example, <b>Mobiles → Apple</b> shows all Apple mobile products from the available marketplaces. Images are intentionally hidden.</p><form method="get"><div class="filters"><div class="field"><label>📱 Choose Category</label><select name="category" onchange="this.form.brand.value='';this.form.submit()"><option value="">Select category</option>{cat_options}</select></div><div class="field"><label>🏷️ Choose Brand</label><select name="brand" onchange="this.form.submit()"><option value="">Select brand</option>{brand_options}</select></div></div><button type="submit">🔎 Compare Products</button></form>{summary}{result}<div class="tip">Prices are compared only from the products available for the selected category and brand.</div></div></div><script>document.querySelectorAll('select').forEach(function(s){{s.addEventListener('change',function(){{s.style.borderColor='#6b5bd5'}})}});</script></body></html>''' 

    return html


# ============================================================
# MARKET INSIGHTS / ANALYTICS
# ============================================================

@app.route(
    "/analytics"
)
def analytics():

    if "username" not in session:

        return redirect(
            "/login"
        )


    summary = (
        marketplace_summary()
    )


    names = [
        "Amazon",
        "Flipkart",
        "Croma",
        "Best Buy"
    ]


    # --------------------------------------------------------
    # CATEGORY DATA
    # --------------------------------------------------------

    category_data = (
        marketplace_df
        .copy()
    )


    if not category_data.empty:

        category_data[
            "category"
        ] = (
            category_data[
                "category"
            ]
            .apply(clean_text)
        )

        category_data = (
            category_data[
                category_data[
                    "category"
                ] != ""
            ]
        )


    if (
        not category_data.empty
    ):

        category = (
            category_data
            .groupby(
                "category"
            )
            .size()
            .reset_index(
                name="count"
            )
            .sort_values(
                "count",
                ascending=False
            )
            .head(12)
        )

        categories = (
            category[
                "category"
            ]
            .astype(str)
            .tolist()
        )

        category_counts = (
            category[
                "count"
            ]
            .astype(int)
            .tolist()
        )

    else:

        categories = []

        category_counts = []


    # --------------------------------------------------------
    # TOP DEALS
    # --------------------------------------------------------

    if marketplace_df.empty:

        insight_products = []

    else:

        insight_products = [

            product_dict(row)

            for _, row
            in marketplace_df.iterrows()

        ]


        insight_products.sort(

            key=lambda product:
                product.get(
                    "deal_score",
                    0
                ),

            reverse=True

        )


        insight_products = (
            insight_products[:10]
        )


    # --------------------------------------------------------
    # OVERALL STATS
    # --------------------------------------------------------

    if marketplace_df.empty:

        total_products = 0
        avg_price = 0
        avg_rating = 0
        avg_discount = 0

    else:

        total_products = int(
            len(
                marketplace_df
            )
        )

        avg_price = round(
            float(
                marketplace_df[
                    "price_inr"
                ].mean()
            ),
            2
        )

        avg_rating = round(
            float(
                marketplace_df[
                    "rating"
                ].mean()
            ),
            2
        )

        avg_discount = round(
            float(
                marketplace_df[
                    "discount"
                ].mean()
            ),
            2
        )


    return render_template(

        "analytics.html",

        marketplace_names=
            names,

        marketplace_counts=[
            int(
                summary
                .get(
                    name.lower(),
                    {}
                )
                .get(
                    "products",
                    0
                )
            )
            for name in names
        ],

        marketplace_percentages=(
            lambda counts: [
                round((v / sum(counts) * 100), 1) if sum(counts) else 0
                for v in counts
            ]
        )([
            int(summary.get(name.lower(), {}).get("products", 0))
            for name in names
        ]),

        marketplace_prices=[
            float(
                summary
                .get(
                    name.lower(),
                    {}
                )
                .get(
                    "price",
                    0
                )
            )
            for name in names
        ],

        marketplace_ratings=[
            float(
                summary
                .get(
                    name.lower(),
                    {}
                )
                .get(
                    "rating",
                    0
                )
            )
            for name in names
        ],

        marketplace_discounts=[
            float(
                summary
                .get(
                    name.lower(),
                    {}
                )
                .get(
                    "discount",
                    0
                )
            )
            for name in names
        ],

        categories=
            categories,

        category_counts=
            category_counts,

        top_products=
            insight_products,

        total_products=
            total_products,

        total_api_products=
            total_products,

        avg_price=
            avg_price,

        avg_rating=
            avg_rating,

        avg_discount=
            avg_discount,
    )


# ============================================================
# REPORT
# ============================================================

@app.route(
    "/report"
)
def report():

    if "username" not in session:

        return redirect(
            "/login"
        )


    summary = (
        marketplace_summary()
    )


    report_data = {}


    for market in MARKETPLACES:

        label = (
            MARKETPLACE_DISPLAY[
                market
            ]
        )

        market_data = (
            summary.get(
                market,
                {}
            )
        )


        report_data[
            f"{label} Products"
        ] = int(
            market_data.get(
                "products",
                0
            )
        )


        report_data[
            f"{label} Average Price"
        ] = float(
            market_data.get(
                "price",
                0
            )
        )


        report_data[
            f"{label} Average Rating"
        ] = float(
            market_data.get(
                "rating",
                0
            )
        )


        report_data[
            f"{label} Average Discount"
        ] = float(
            market_data.get(
                "discount",
                0
            )
        )


    return render_template(
        "report.html",
        report=report_data
    )


# ============================================================
# BEST DEALS
# ============================================================

@app.route(
    "/best-deals"
)
def best_deals():

    if "username" not in session:

        return redirect(
            "/login"
        )


    if marketplace_df.empty:

        deals = []

    else:

        data = (
            marketplace_df
            .copy()
        )


        data[
            "deal_score_temp"
        ] = (
            data.apply(
                deal_score,
                axis=1
            )
        )


        data = (
            data
            .sort_values(
                "deal_score_temp",
                ascending=False
            )
            .head(60)
        )


        deals = [
            product_dict(row)
            for _, row
            in data.iterrows()
        ]


    return render_template(
        "best_deals.html",
        deals=deals
    )


# ============================================================
# API SEARCH
# ============================================================

@app.route(
    "/api/products"
)
def api_products():

    if "username" not in session:

        return jsonify(
            {
                "error":
                    "Unauthorized"
            }
        ), 401


    query = request.args.get(
        "q",
        ""
    ).strip()


    marketplace = request.args.get(
        "marketplace",
        ""
    ).strip()


    results = search_products(
        query,
        marketplace,
        60
    )


    return jsonify({

        "count":
            len(results),

        "products":
            results

    })


# ============================================================
# OLD API PRODUCTS ROUTE
# ============================================================

@app.route(
    "/api-products"
)
def old_api_products():

    return redirect(
        "/search"
    )


# ============================================================
# ERROR HANDLERS
# ============================================================

@app.errorhandler(404)
def page_not_found(
    error
):

    return (
        "<h2>404 - Page Not Found</h2>",
        404
    )


@app.errorhandler(500)
def internal_error(
    error
):

    print(
        "Internal server error:",
        error
    )

    return (
        "<h2>500 - Internal Server Error</h2>"
        "<p>Please check the Flask terminal.</p>",
        500
    )


# ============================================================
# MARKET INSIGHTS CHART LABELS
# ============================================================

@app.after_request
def add_market_insights_chart_labels(response):
    """Add value/percentage labels to analytics bar charts from app.py."""
    try:
        if request.path == "/analytics" and "text/html" in response.content_type:
            html = response.get_data(as_text=True)
            script = r'''<script>
(function () {
  function installMarketInsightLabels() {
    if (!window.Chart || window.__marketInsightLabelsInstalled) return;
    window.__marketInsightLabelsInstalled = true;
    const plugin = {
      id: 'marketInsightLabels',
      afterDatasetsDraw(chart) {
        if (!chart || chart.config.type !== 'bar') return;
        const ctx = chart.ctx;
        ctx.save();
        chart.data.datasets.forEach((dataset, di) => {
          const meta = chart.getDatasetMeta(di);
          meta.data.forEach((bar, i) => {
            const value = Number(dataset.data[i]);
            if (!Number.isFinite(value) || value <= 0) return;
            // Calculate the share of the entire chart, not 100% for every bar.
            const total = chart.data.datasets.reduce((sum, ds) => {
              return sum + ds.data.reduce((inner, raw) => {
                const n = Number(raw);
                return inner + (Number.isFinite(n) ? Math.max(0, n) : 0);
              }, 0);
            }, 0);
            const pct = total ? (value / total * 100) : 0;
            ctx.font = '600 12px Arial';
            ctx.textAlign = 'center';
            ctx.textBaseline = 'bottom';
            ctx.fillStyle = '#1f2937';
            const label = Number.isInteger(value) ? value.toLocaleString() : value.toFixed(1);
            ctx.fillText(label + ' (' + pct.toFixed(1) + '%)', bar.x, bar.y - 6);
          });
        });
        ctx.restore();
      }
    };
    Chart.register(plugin);
    if (Chart.instances) {
      Object.values(Chart.instances).forEach(c => { try { c.update(); } catch(e) {} });
    }
  }
  const wait = setInterval(() => {
    if (window.Chart) { clearInterval(wait); installMarketInsightLabels(); }
  }, 100);
  setTimeout(() => clearInterval(wait), 10000);
})();
</script>'''
            if "</body>" in html:
                html = html.replace("</body>", script + "</body>")
                response.set_data(html)
    except Exception:
        pass
    return response


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":

    print()
    print(
        "=" * 60
    )

    print(
        " AUTOMATED MARKET & TREND INTELLIGENCE BOT"
    )

    print(
        "=" * 60
    )


    if marketplace_df.empty:

        print(
            "WARNING: all_marketplaces.csv "
            "could not be loaded."
        )

    else:

        print(
            f"Total products loaded: "
            f"{len(marketplace_df)}"
        )


        for market in MARKETPLACES:

            count = len(
                marketplace_df[
                    marketplace_df[
                        "marketplace"
                    ]
                    ==
                    market
                ]
            )

            print(
                f"{MARKETPLACE_DISPLAY[market]:10} : "
                f"{count} products"
            )


    print(
        "=" * 60
    )

    print(
        "Server: http://127.0.0.1:5000"
    )

    print(
        "=" * 60
    )

    print()


    app.run(
        debug=True,
        host="127.0.0.1",
        port=5000
    )