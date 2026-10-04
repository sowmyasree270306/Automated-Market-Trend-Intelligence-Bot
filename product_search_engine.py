# product_search_engine.py

import os
import re
import sqlite3
from typing import List, Dict, Any, Optional

import pandas as pd
from rapidfuzz import fuzz


# ============================================================
# PATHS
# ============================================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATASET_DIR = os.path.join(BASE_DIR, "dataset")

CSV_FILE = os.path.join(DATASET_DIR, "all_marketplaces.csv")
DB_FILE = os.path.join(BASE_DIR, "database.db")


# ============================================================
# SETTINGS
# ============================================================

MAX_RESULTS = 60

MARKETPLACES = [
    "Amazon",
    "Flipkart",
    "Walmart",
    "Target"
]


# ============================================================
# LOAD DATA
# ============================================================

def load_products() -> pd.DataFrame:
    """
    Load the combined four-marketplace dataset.
    """

    if not os.path.exists(CSV_FILE):
        print("ERROR: all_marketplaces.csv not found:")
        print(CSV_FILE)
        return pd.DataFrame()

    try:
        df = pd.read_csv(CSV_FILE)

        # Standard column names
        df.columns = [
            str(col).strip().lower().replace(" ", "_")
            for col in df.columns
        ]

        # Make sure required columns exist
        required_columns = [
            "marketplace",
            "product_name",
            "price"
        ]

        for column in required_columns:
            if column not in df.columns:
                df[column] = ""

        # Optional columns
        optional_columns = [
            "product_id",
            "brand",
            "category",
            "mrp",
            "discount",
            "rating",
            "reviews",
            "currency",
            "image",
            "product_url",
            "availability",
            "price_inr"
        ]

        for column in optional_columns:
            if column not in df.columns:
                df[column] = ""

        # Clean text columns
        text_columns = [
            "marketplace",
            "product_name",
            "brand",
            "category",
            "currency",
            "image",
            "product_url",
            "availability"
        ]

        for column in text_columns:
            df[column] = df[column].fillna("").astype(str).str.strip()

        # Numeric conversion
        numeric_columns = [
            "price",
            "price_inr",
            "mrp",
            "discount",
            "rating",
            "reviews"
        ]

        for column in numeric_columns:
            df[column] = pd.to_numeric(
                df[column],
                errors="coerce"
            )

        # If price_inr is available, use it
        # Otherwise use price
        df["final_price"] = df["price_inr"]

        df["final_price"] = df["final_price"].fillna(
            df["price"]
        )

        # Remove invalid prices
        df = df[
            (df["final_price"].notna()) &
            (df["final_price"] > 0)
        ].copy()

        # Normalize marketplace names
        df["marketplace"] = df["marketplace"].apply(
            normalize_marketplace
        )

        return df.reset_index(drop=True)

    except Exception as e:
        print("ERROR loading dataset:", e)
        return pd.DataFrame()


# ============================================================
# MARKETPLACE NORMALIZATION
# ============================================================

def normalize_marketplace(value: Any) -> str:

    value = str(value).strip()

    lower = value.lower()

    if "amazon" in lower:
        return "Amazon"

    if "flipkart" in lower:
        return "Flipkart"

    if "walmart" in lower:
        return "Walmart"

    if "target" in lower:
        return "Target"

    return value


# ============================================================
# TEXT NORMALIZATION
# ============================================================

def clean_text(text: Any) -> str:

    if text is None:
        return ""

    text = str(text).lower()

    # Remove special characters
    text = re.sub(r"[^a-z0-9\s]", " ", text)

    # Normalize whitespace
    text = re.sub(r"\s+", " ", text).strip()

    return text


def tokenize(text: Any) -> List[str]:

    text = clean_text(text)

    if not text:
        return []

    return text.split()


# ============================================================
# PRODUCT TYPE DETECTION
# ============================================================

PRODUCT_TYPE_KEYWORDS = {

    "laptop": [
        "laptop",
        "notebook",
        "macbook",
        "chromebook",
        "thinkpad",
        "ideapad",
        "vivobook",
        "zenbook",
        "pavilion",
        "inspiron",
        "latitude",
        "precision",
        "rog",
        "tuf gaming"
    ],

    "phone": [
        "iphone",
        "smartphone",
        "mobile phone",
        "galaxy",
        "redmi",
        "poco",
        "pixel",
        "oneplus",
        "realme",
        "oppo",
        "vivo",
        "motorola",
        "nokia"
    ],

    "tablet": [
        "tablet",
        "ipad",
        "galaxy tab",
        "tab s",
        "tab a"
    ],

    "television": [
        "television",
        "tv",
        "smart tv",
        "led tv",
        "oled tv",
        "qled tv"
    ],

    "headphones": [
        "headphone",
        "headphones",
        "earphone",
        "earphones",
        "earbud",
        "earbuds",
        "airpods",
        "headset"
    ],

    "watch": [
        "smartwatch",
        "smart watch",
        "apple watch",
        "galaxy watch"
    ],

    "camera": [
        "camera",
        "dslr",
        "mirrorless",
        "digital camera"
    ]
}


# ============================================================
# ACCESSORY / NON-PRODUCT WORDS
# ============================================================

ACCESSORY_WORDS = {
    "accessory",
    "accessories",
    "bag",
    "bags",
    "backpack",
    "backpacks",
    "sleeve",
    "sleeves",
    "case",
    "cases",
    "cover",
    "covers",
    "screen",
    "protector",
    "protectors",
    "stand",
    "stands",
    "holder",
    "holders",
    "mount",
    "mounts",
    "tripod",
    "tripods",
    "charger",
    "chargers",
    "charging",
    "cable",
    "cables",
    "adapter",
    "adapters",
    "dock",
    "docks",
    "hub",
    "hubs",
    "keyboard",
    "keyboards",
    "mouse",
    "mice",
    "speaker",
    "speakers",
    "table",
    "tables",
    "desk",
    "desks",
    "sleeve",
    "sleeves",
    "skin",
    "skins",
    "sticker",
    "stickers",
    "strap",
    "straps",
    "replacement",
    "replacement",
    "battery",
    "batteries",
    "stylus",
    "pen",
    "pens",
    "remote",
    "remotes",
    "cleaning",
    "cleaner",
    "protector"
}


# ============================================================
# CATEGORY ACCESSORY WORDS
# ============================================================

ACCESSORY_CATEGORIES = {
    "accessories",
    "bags",
    "cases",
    "covers",
    "chargers",
    "cables",
    "electronics accessories",
    "computer accessories",
    "mobile accessories",
    "phone accessories",
    "laptop accessories",
    "keyboard",
    "mouse",
    "computer peripherals",
    "stands",
    "holders",
    "tables",
    "furniture"
}


# ============================================================
# PRODUCT TYPE
# ============================================================

def detect_product_type(query: str) -> str:

    query_clean = clean_text(query)

    # More specific types first
    if any(
        keyword in query_clean
        for keyword in [
            "iphone",
            "smartphone",
            "mobile phone",
            "galaxy",
            "redmi",
            "poco",
            "pixel",
            "oneplus",
            "realme",
            "oppo",
            "vivo",
            "motorola",
            "nokia"
        ]
    ):
        return "phone"

    if any(
        keyword in query_clean
        for keyword in PRODUCT_TYPE_KEYWORDS["tablet"]
    ):
        return "tablet"

    if any(
        keyword in query_clean
        for keyword in PRODUCT_TYPE_KEYWORDS["laptop"]
    ):
        return "laptop"

    if any(
        keyword in query_clean
        for keyword in PRODUCT_TYPE_KEYWORDS["television"]
    ):
        return "television"

    if any(
        keyword in query_clean
        for keyword in PRODUCT_TYPE_KEYWORDS["headphones"]
    ):
        return "headphones"

    if any(
        keyword in query_clean
        for keyword in PRODUCT_TYPE_KEYWORDS["watch"]
    ):
        return "watch"

    if any(
        keyword in query_clean
        for keyword in PRODUCT_TYPE_KEYWORDS["camera"]
    ):
        return "camera"

    return "general"


# ============================================================
# ACCESSORY DETECTION
# ============================================================

def contains_accessory_word(text: str) -> bool:

    tokens = set(tokenize(text))

    return bool(tokens.intersection(ACCESSORY_WORDS))


def is_accessory_category(category: str) -> bool:

    category_clean = clean_text(category)

    if not category_clean:
        return False

    for word in ACCESSORY_CATEGORIES:

        if clean_text(word) in category_clean:
            return True

    return False


# ============================================================
# PRODUCT RELEVANCE FILTER
# ============================================================

def is_relevant_product(
    query: str,
    product_name: str,
    category: str = "",
    brand: str = ""
) -> bool:

    query_clean = clean_text(query)
    name_clean = clean_text(product_name)
    category_clean = clean_text(category)
    brand_clean = clean_text(brand)

    if not name_clean:
        return False

    product_type = detect_product_type(query_clean)

    # --------------------------------------------------------
    # COMMON ACCESSORY FILTER
    # --------------------------------------------------------

    # Reject obvious accessories when searching for actual
    # consumer products.
    if product_type in {
        "laptop",
        "phone",
        "tablet",
        "television",
        "camera",
        "watch"
    }:

        name_tokens = set(tokenize(name_clean))

        if name_tokens.intersection(ACCESSORY_WORDS):
            return False

        if is_accessory_category(category_clean):
            return False

    # --------------------------------------------------------
    # LAPTOP SEARCH
    # --------------------------------------------------------

    if product_type == "laptop":

        laptop_identifiers = {
            "laptop",
            "notebook",
            "macbook",
            "chromebook",
            "thinkpad",
            "ideapad",
            "vivobook",
            "zenbook",
            "pavilion",
            "inspiron",
            "latitude",
            "precision",
            "rog",
            "tuf"
        }

        # Reject accessory terms again
        if contains_accessory_word(name_clean):
            return False

        # Reject laptop accessory categories
        laptop_bad_categories = {
            "bags",
            "backpacks",
            "laptop bags",
            "laptop accessories",
            "cases",
            "covers",
            "stands",
            "tables",
            "desks",
            "keyboard",
            "mouse",
            "chargers",
            "cables",
            "computer accessories"
        }

        for bad_category in laptop_bad_categories:

            if bad_category in category_clean:
                return False

        # Actual laptop model/product indicators
        has_laptop_identifier = any(
            word in name_clean
            for word in laptop_identifiers
        )

        # If query is exactly "laptop", require an actual
        # laptop/notebook/model indicator.
        if query_clean in {
            "laptop",
            "laptops",
            "notebook",
            "notebooks"
        }:

            if not has_laptop_identifier:
                return False

            return True

        # For specific laptop searches, the product should
        # contain at least one laptop identifier.
        query_tokens = set(tokenize(query_clean))

        identifier_match = any(
            token in name_clean
            for token in laptop_identifiers
        )

        if not identifier_match:
            return False

        # Check important query words
        meaningful_tokens = [
            token
            for token in query_tokens
            if len(token) >= 2
        ]

        if meaningful_tokens:

            matched = sum(
                1
                for token in meaningful_tokens
                if token in name_clean
                or token in brand_clean
            )

            # At least one meaningful query token
            if matched == 0:
                return False

        return True

    # --------------------------------------------------------
    # PHONE SEARCH
    # --------------------------------------------------------

    if product_type == "phone":

        phone_identifiers = [
            "iphone",
            "galaxy",
            "redmi",
            "poco",
            "pixel",
            "oneplus",
            "realme",
            "oppo",
            "vivo",
            "motorola",
            "nokia",
            "smartphone"
        ]

        if not any(
            word in name_clean
            for word in phone_identifiers
        ):
            return False

        # Accessories are already rejected above
        return True

    # --------------------------------------------------------
    # TABLET SEARCH
    # --------------------------------------------------------

    if product_type == "tablet":

        tablet_identifiers = [
            "tablet",
            "ipad",
            "galaxy tab",
            "tab s",
            "tab a"
        ]

        if not any(
            word in name_clean
            for word in tablet_identifiers
        ):
            return False

        return True

    # --------------------------------------------------------
    # TELEVISION SEARCH
    # --------------------------------------------------------

    if product_type == "television":

        tv_identifiers = [
            "tv",
            "television",
            "smart tv",
            "led tv",
            "oled",
            "qled"
        ]

        if not any(
            word in name_clean
            for word in tv_identifiers
        ):
            return False

        return True

    # --------------------------------------------------------
    # HEADPHONES SEARCH
    # --------------------------------------------------------

    if product_type == "headphones":

        headphone_identifiers = [
            "headphone",
            "earphone",
            "earbud",
            "airpods",
            "headset"
        ]

        if not any(
            word in name_clean
            for word in headphone_identifiers
        ):
            return False

        return True

    # --------------------------------------------------------
    # SMARTWATCH SEARCH
    # --------------------------------------------------------

    if product_type == "watch":

        watch_identifiers = [
            "watch",
            "smartwatch",
            "smart watch"
        ]

        if not any(
            word in name_clean
            for word in watch_identifiers
        ):
            return False

        return True

    # --------------------------------------------------------
    # CAMERA SEARCH
    # --------------------------------------------------------

    if product_type == "camera":

        camera_identifiers = [
            "camera",
            "dslr",
            "mirrorless"
        ]

        if not any(
            word in name_clean
            for word in camera_identifiers
        ):
            return False

        return True

    # --------------------------------------------------------
    # GENERAL SEARCH
    # --------------------------------------------------------

    return True


# ============================================================
# QUERY TOKENS
# ============================================================

def get_query_tokens(query: str) -> List[str]:

    tokens = tokenize(query)

    # Remove generic search words
    stop_words = {
        "best",
        "buy",
        "online",
        "price",
        "prices",
        "product",
        "products",
        "available",
        "find",
        "search",
        "show",
        "me",
        "cheap",
        "cheapest",
        "latest",
        "new"
    }

    return [
        token
        for token in tokens
        if token not in stop_words
        and len(token) >= 2
    ]


# ============================================================
# SEARCH SCORE
# ============================================================

def calculate_match_score(
    query: str,
    product_name: str,
    brand: str = "",
    category: str = ""
) -> float:

    query_clean = clean_text(query)
    name_clean = clean_text(product_name)
    brand_clean = clean_text(brand)
    category_clean = clean_text(category)

    if not query_clean or not name_clean:
        return 0.0

    # Full string similarity
    ratio_score = fuzz.ratio(
        query_clean,
        name_clean
    )

    partial_score = fuzz.partial_ratio(
        query_clean,
        name_clean
    )

    token_score = fuzz.token_set_ratio(
        query_clean,
        name_clean
    )

    # Token matching
    query_tokens = get_query_tokens(query)

    matched_tokens = 0

    for token in query_tokens:

        if (
            token in name_clean
            or token in brand_clean
        ):
            matched_tokens += 1

    token_match_score = 0

    if query_tokens:
        token_match_score = (
            matched_tokens /
            len(query_tokens)
        ) * 100

    # Exact phrase bonus
    exact_bonus = 0

    if query_clean in name_clean:
        exact_bonus = 15

    # Brand bonus
    brand_bonus = 0

    if brand_clean and brand_clean in query_clean:
        brand_bonus = 10

    score = (
        ratio_score * 0.20 +
        partial_score * 0.20 +
        token_score * 0.35 +
        token_match_score * 0.20 +
        exact_bonus +
        brand_bonus
    )

    return min(round(score, 2), 100.0)


# ============================================================
# DEAL SCORE
# ============================================================

def calculate_deal_score(
    price: float,
    mrp: float = 0,
    discount: float = 0,
    rating: float = 0,
    reviews: float = 0
) -> float:

    try:
        price = float(price or 0)
    except Exception:
        price = 0

    try:
        mrp = float(mrp or 0)
    except Exception:
        mrp = 0

    try:
        discount = float(discount or 0)
    except Exception:
        discount = 0

    try:
        rating = float(rating or 0)
    except Exception:
        rating = 0

    try:
        reviews = float(reviews or 0)
    except Exception:
        reviews = 0

    # Calculate discount if dataset discount is unavailable
    if discount <= 0 and mrp > price and price > 0:

        discount = (
            (mrp - price) /
            mrp
        ) * 100

    # Price component
    price_score = 0

    if price > 0 and mrp > 0:

        price_ratio = price / mrp

        price_score = max(
            0,
            min(
                100,
                (1 - price_ratio) * 100
            )
        )

    # Discount component
    discount_score = min(
        max(discount, 0),
        100
    )

    # Rating component
    rating_score = min(
        max((rating / 5) * 100, 0),
        100
    )

    # Review score
    if reviews > 0:
        review_score = min(
            100,
            (reviews / 10000) * 100
        )
    else:
        review_score = 0

    score = (
        price_score * 0.40 +
        discount_score * 0.20 +
        rating_score * 0.20 +
        review_score * 0.20
    )

    return round(score, 2)


# ============================================================
# STANDARDIZE RESULT
# ============================================================

def standardize_result(row: pd.Series) -> Dict[str, Any]:

    marketplace = normalize_marketplace(
        row.get("marketplace", "")
    )

    product_name = str(
        row.get("product_name", "")
    ).strip()

    brand = str(
        row.get("brand", "")
    ).strip()

    category = str(
        row.get("category", "")
    ).strip()

    product_id = str(
        row.get("product_id", "")
    ).strip()

    image = str(
        row.get("image", "")
    ).strip()

    product_url = str(
        row.get("product_url", "")
    ).strip()

    availability = str(
        row.get("availability", "")
    ).strip()

    if availability == "":
        availability = "Available"

    # Price
    price_value = row.get("final_price", 0)

    try:
        price = float(price_value)
    except Exception:
        price = 0.0

    # MRP
    try:
        mrp = float(row.get("mrp", 0) or 0)
    except Exception:
        mrp = 0.0

    # Discount
    try:
        discount = float(
            row.get("discount", 0) or 0
        )
    except Exception:
        discount = 0.0

    # Rating
    try:
        rating = float(
            row.get("rating", 0) or 0
        )
    except Exception:
        rating = 0.0

    # Reviews
    try:
        reviews = float(
            row.get("reviews", 0) or 0
        )
    except Exception:
        reviews = 0.0

    return {
        "marketplace": marketplace,
        "product_id": product_id,
        "product_name": product_name,
        "brand": brand,
        "category": category,

        "price": round(price, 2),
        "price_inr": round(price, 2),
        "mrp": round(mrp, 2),
        "discount": round(discount, 2),

        "rating": round(rating, 2),
        "reviews": int(reviews) if reviews >= 0 else 0,

        "currency": str(
            row.get("currency", "INR")
        ).strip() or "INR",

        "image": image,
        "product_url": product_url,

        # Used by older templates
        "url": product_url,

        "availability": availability,

        "match_score": 0.0,
        "deal_score": 0.0,

        "is_best_price": False,
        "best_price": False
    }


# ============================================================
# REMOVE DUPLICATES
# ============================================================

def remove_duplicate_products(
    products: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:

    seen = set()
    output = []

    for product in products:

        name = clean_text(
            product.get("product_name", "")
        )

        marketplace = product.get(
            "marketplace",
            ""
        )

        key = (
            marketplace,
            name
        )

        if key in seen:
            continue

        seen.add(key)
        output.append(product)

    return output


# ============================================================
# SEARCH
# ============================================================

def search_all(
    query: str,
    marketplace: Optional[str] = None,
    max_results: int = MAX_RESULTS
) -> List[Dict[str, Any]]:
    """
    Main search function used by Flask app.py.

    Example:
        search_all("iphone 14")
        search_all("laptop")
        search_all("iphone", "Flipkart")
    """

    query = str(query or "").strip()

    if not query:
        return []

    df = load_products()

    if df.empty:
        return []

    # --------------------------------------------------------
    # Marketplace filter
    # --------------------------------------------------------

    if marketplace:

        marketplace_clean = normalize_marketplace(
            marketplace
        )

        if marketplace_clean.lower() not in {
            "all",
            ""
        }:

            df = df[
                df["marketplace"].str.lower()
                == marketplace_clean.lower()
            ].copy()

    if df.empty:
        return []

    # --------------------------------------------------------
    # Product filtering
    # --------------------------------------------------------

    relevant_rows = []

    for _, row in df.iterrows():

        product_name = row.get(
            "product_name",
            ""
        )

        category = row.get(
            "category",
            ""
        )

        brand = row.get(
            "brand",
            ""
        )

        if not is_relevant_product(
            query,
            product_name,
            category,
            brand
        ):
            continue

        relevant_rows.append(row)

    if not relevant_rows:
        return []

    # --------------------------------------------------------
    # Score products
    # --------------------------------------------------------

    scored_products = []

    for row in relevant_rows:

        product_name = row.get(
            "product_name",
            ""
        )

        brand = row.get(
            "brand",
            ""
        )

        category = row.get(
            "category",
            ""
        )

        match_score = calculate_match_score(
            query,
            product_name,
            brand,
            category
        )

        result = standardize_result(row)

        result["match_score"] = match_score

        result["deal_score"] = calculate_deal_score(
            result["price"],
            result["mrp"],
            result["discount"],
            result["rating"],
            result["reviews"]
        )

        scored_products.append(result)

    # --------------------------------------------------------
    # Minimum relevance
    # --------------------------------------------------------

    product_type = detect_product_type(query)

    if product_type != "general":

        scored_products = [
            product
            for product in scored_products
            if product["match_score"] >= 35
        ]

    else:

        scored_products = [
            product
            for product in scored_products
            if product["match_score"] >= 25
        ]

    # --------------------------------------------------------
    # Remove duplicates
    # --------------------------------------------------------

    scored_products = remove_duplicate_products(
        scored_products
    )

    # --------------------------------------------------------
    # Sort
    #
    # Match relevance first, then deal score.
    # --------------------------------------------------------

    scored_products.sort(
        key=lambda x: (
            x.get("match_score", 0),
            x.get("deal_score", 0)
        ),
        reverse=True
    )

    # --------------------------------------------------------
    # Best price
    #
    # This marks the lowest price among the matching
    # search results.
    # --------------------------------------------------------

    valid_prices = [
        float(product["price"])
        for product in scored_products
        if product.get("price", 0) > 0
    ]

    if valid_prices:

        lowest_price = min(valid_prices)

        for product in scored_products:

            if (
                product.get("price", 0)
                == lowest_price
            ):

                product["is_best_price"] = True
                product["best_price"] = True

    # --------------------------------------------------------
    # Limit results
    # --------------------------------------------------------

    scored_products = scored_products[
        :max_results
    ]

    return scored_products


# ============================================================
# BEST PRICE
# ============================================================

def get_best_price(
    products: List[Dict[str, Any]]
) -> Optional[Dict[str, Any]]:

    valid_products = [
        product
        for product in products
        if product.get("price", 0) > 0
    ]

    if not valid_products:
        return None

    return min(
        valid_products,
        key=lambda x: float(
            x.get("price", 0)
        )
    )


# ============================================================
# MARKETPLACE PRICE SUMMARY
# ============================================================

def marketplace_price_summary(
    products: List[Dict[str, Any]]
) -> Dict[str, Dict[str, Any]]:

    summary = {}

    for marketplace in MARKETPLACES:

        marketplace_products = [
            product
            for product in products
            if product.get("marketplace")
            == marketplace
            and product.get("price", 0) > 0
        ]

        if not marketplace_products:

            summary[marketplace] = {
                "available": False,
                "price": None,
                "product": None
            }

            continue

        best = min(
            marketplace_products,
            key=lambda x: float(
                x.get("price", 0)
            )
        )

        summary[marketplace] = {
            "available": True,
            "price": best.get("price"),
            "product": best
        }

    return summary


# ============================================================
# DATABASE SEARCH
# ============================================================

def search_database(
    query: str,
    marketplace: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Optional SQLite search.

    This does NOT call QuickCommerce API.
    """

    if not os.path.exists(DB_FILE):
        return []

    try:

        connection = sqlite3.connect(DB_FILE)

        cursor = connection.cursor()

        if marketplace:

            cursor.execute(
                """
                SELECT *
                FROM marketplace_products
                WHERE LOWER(product_name) LIKE ?
                AND LOWER(marketplace) = ?
                LIMIT 100
                """,
                (
                    f"%{query.lower()}%",
                    marketplace.lower()
                )
            )

        else:

            cursor.execute(
                """
                SELECT *
                FROM marketplace_products
                WHERE LOWER(product_name) LIKE ?
                LIMIT 100
                """,
                (
                    f"%{query.lower()}%",
                )
            )

        rows = cursor.fetchall()

        columns = [
            description[0]
            for description in cursor.description
        ]

        connection.close()

        return [
            dict(zip(columns, row))
            for row in rows
        ]

    except Exception:
        return []


# ============================================================
# TEST SEARCH
# ============================================================

def print_results(
    query: str,
    results: List[Dict[str, Any]]
):

    print()
    print("=" * 80)
    print("SEARCH:", query)
    print("PRODUCT TYPE:", detect_product_type(query))
    print("RESULTS:", len(results))
    print("=" * 80)

    if not results:

        print("No matching products found.")
        return

    for index, product in enumerate(
        results,
        start=1
    ):

        best_text = ""

        if product.get("is_best_price"):
            best_text = " ⭐ BEST PRICE"

        print()
        print(
            f"{index}. "
            f"{product.get('marketplace')} | "
            f"{product.get('product_name')}"
        )

        print(
            f"   Price: ₹{product.get('price')}"
        )

        print(
            f"   Match: "
            f"{product.get('match_score')} | "
            f"Deal: "
            f"{product.get('deal_score')}"
            f"{best_text}"
        )

        print(
            f"   Rating: "
            f"{product.get('rating')} | "
            f"Reviews: "
            f"{product.get('reviews')}"
        )


# ============================================================
# COMMAND LINE TEST
# ============================================================

if __name__ == "__main__":

    print("=" * 80)
    print("AUTOMATED MARKET & TREND INTELLIGENCE BOT")
    print("Product Search Engine")
    print("=" * 80)

    user_query = input(
        "Enter product to search: "
    ).strip()

    results = search_all(
        user_query
    )

    print_results(
        user_query,
        results
    )

    best = get_best_price(results)

    print()

    if best:

        print("=" * 80)
        print("BEST PRICE")
        print("=" * 80)

        print(
            "Marketplace:",
            best.get("marketplace")
        )

        print(
            "Product:",
            best.get("product_name")
        )

        print(
            "Price: ₹",
            best.get("price")
        )

    else:

        print("No best price available.")