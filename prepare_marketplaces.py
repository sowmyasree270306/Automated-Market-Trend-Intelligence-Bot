# ============================================================
# AUTOMATED MARKET & TREND INTELLIGENCE BOT
# MARKETPLACE DATA PREPARATION
# ============================================================
#
# Project structure:
#
# Automated_Market_Trend_Bot_API/
# │
# ├── app.py
# ├── prepare_marketplaces.py
# │
# └── dataset/
#     ├── merged_electronics_dataset.csv
#     ├── flipkart_products_new.csv
#     ├── walmart-products.csv
#     ├── BestBuy_Products.csv
#     └── all_marketplaces.csv
#
# Output:
#     dataset/all_marketplaces.csv
#
# Marketplace order:
#     Amazon → Flipkart → Walmart → Best Buy
# ============================================================

import os
import re
import ast
import json
import pandas as pd


# ============================================================
# PATHS
# ============================================================

# prepare_marketplaces.py is in the PROJECT ROOT
BASE_DIR = os.path.dirname(
    os.path.abspath(__file__)
)

DATASET_DIR = os.path.join(
    BASE_DIR,
    "dataset"
)

OUTPUT_FILE = os.path.join(
    DATASET_DIR,
    "all_marketplaces.csv"
)

# Input files
AMAZON_FILE = os.path.join(
    DATASET_DIR,
    "merged_electronics_dataset.csv"
)

FLIPKART_FILE = os.path.join(
    DATASET_DIR,
    "flipkart_products_new.csv"
)

WALMART_FILE = os.path.join(
    DATASET_DIR,
    "walmart-products.csv"
)

BESTBUY_FILE = os.path.join(
    DATASET_DIR,
    "BestBuy_Products.csv"
)


# ============================================================
# SETTINGS
# ============================================================

# Historical Walmart / Best Buy datasets may use USD.
# This is only used to create a common INR comparison value.
USD_TO_INR = 85.0

FINAL_COLUMNS = [
    "marketplace",
    "product_id",
    "product_name",
    "brand",
    "category",
    "price",
    "mrp",
    "discount",
    "rating",
    "reviews",
    "currency",
    "image",
    "product_url",
    "availability",
    "original_currency",
    "original_price",
    "price_inr",
]


# ============================================================
# BASIC HELPERS
# ============================================================

def clean_text(value):

    if value is None:
        return ""

    try:
        if pd.isna(value):
            return ""
    except Exception:
        pass

    text = str(value).strip()

    if text.lower() in {
        "nan",
        "none",
        "null",
        "na",
        "n/a"
    }:
        return ""

    return text


def clean_number(value):

    if value is None:
        return 0.0

    try:
        if pd.isna(value):
            return 0.0
    except Exception:
        pass

    if isinstance(value, (int, float)):

        try:
            return float(value)
        except Exception:
            return 0.0

    text = str(value).strip()

    if not text:
        return 0.0

    text = (
        text
        .replace("₹", "")
        .replace("$", "")
        .replace("€", "")
        .replace("£", "")
        .replace(",", "")
        .strip()
    )

    match = re.search(
        r"-?\d+(?:\.\d+)?",
        text
    )

    if not match:
        return 0.0

    try:
        return float(
            match.group(0)
        )
    except Exception:
        return 0.0


def clean_rating(value):

    rating = clean_number(value)

    return max(
        0.0,
        min(
            5.0,
            rating
        )
    )


def first_column(
    df,
    possible_columns
):

    for column in possible_columns:

        if column in df.columns:
            return column

    return None


def get_text_column(
    df,
    possible_columns
):

    column = first_column(
        df,
        possible_columns
    )

    if column is None:

        return pd.Series(
            "",
            index=df.index,
            dtype="object"
        )

    return df[column].apply(
        clean_text
    )


def get_number_column(
    df,
    possible_columns
):

    column = first_column(
        df,
        possible_columns
    )

    if column is None:

        return pd.Series(
            0.0,
            index=df.index,
            dtype="float64"
        )

    return df[column].apply(
        clean_number
    )


def calculate_discount(
    price,
    mrp
):

    price = clean_number(price)
    mrp = clean_number(mrp)

    if (
        price <= 0
        or mrp <= 0
        or mrp < price
    ):
        return 0.0

    discount = (
        (mrp - price)
        / mrp
        * 100
    )

    return round(
        max(
            0.0,
            min(
                100.0,
                discount
            )
        ),
        2
    )


def safe_read_csv(path):

    if not os.path.exists(path):

        print()
        print(
            "ERROR: File not found:"
        )
        print(
            path
        )

        return pd.DataFrame()

    try:

        return pd.read_csv(
            path,
            low_memory=False
        )

    except Exception as error:

        print()
        print(
            "ERROR: Could not read:"
        )
        print(
            path
        )
        print(
            error
        )

        return pd.DataFrame()


def make_fallback_id(
    marketplace,
    index
):

    return (
        marketplace
        + "_"
        + str(index + 1)
    )


def ensure_ids(
    result,
    marketplace
):

    result["product_id"] = (
        result["product_id"]
        .apply(clean_text)
    )

    for index in result.index:

        if not result.at[
            index,
            "product_id"
        ]:

            result.at[
                index,
                "product_id"
            ] = make_fallback_id(
                marketplace,
                index
            )

    return result


# ============================================================
# IMAGE / URL HELPERS
# ============================================================

def parse_list_first(value):

    text = clean_text(value)

    if not text:
        return ""

    if (
        text.startswith("http://")
        or text.startswith("https://")
    ):
        return text

    # Python list format
    try:

        parsed = ast.literal_eval(
            text
        )

        if isinstance(
            parsed,
            (list, tuple)
        ) and parsed:

            return clean_text(
                parsed[0]
            )

        if isinstance(
            parsed,
            dict
        ):

            for item in parsed.values():

                item = clean_text(
                    item
                )

                if (
                    item.startswith(
                        "http://"
                    )
                    or
                    item.startswith(
                        "https://"
                    )
                ):

                    return item

    except Exception:
        pass

    # JSON list format
    try:

        parsed = json.loads(
            text
        )

        if (
            isinstance(
                parsed,
                list
            )
            and parsed
        ):

            return clean_text(
                parsed[0]
            )

    except Exception:
        pass

    # Search for URL inside text
    match = re.search(
        r"https?://[^\s\"'\]]+",
        text
    )

    if match:
        return match.group(0)

    return ""


def parse_availability(value):

    text = clean_text(
        value
    )

    if not text:
        return "Available"

    lower = text.lower()

    if lower in {
        "true",
        "1",
        "yes",
        "available",
        "in stock",
        "instock"
    }:
        return "Available"

    if lower in {
        "false",
        "0",
        "no",
        "unavailable",
        "out of stock",
        "outofstock"
    }:
        return "Unavailable"

    return text


# ============================================================
# NORMALIZE RESULT
# ============================================================

def normalize_result(
    result,
    marketplace
):

    # Make sure all columns exist
    for column in FINAL_COLUMNS:

        if column not in result.columns:

            result[column] = ""

    # Text columns
    text_columns = [
        "marketplace",
        "product_id",
        "product_name",
        "brand",
        "category",
        "currency",
        "image",
        "product_url",
        "availability",
        "original_currency",
    ]

    for column in text_columns:

        result[column] = (
            result[column]
            .apply(clean_text)
        )

    # Numeric columns
    numeric_columns = [
        "price",
        "mrp",
        "discount",
        "rating",
        "reviews",
        "original_price",
        "price_inr",
    ]

    for column in numeric_columns:

        result[column] = pd.to_numeric(
            result[column],
            errors="coerce"
        ).fillna(0.0)

    result["rating"] = (
        result["rating"]
        .clip(0, 5)
        .round(2)
    )

    result["discount"] = (
        result["discount"]
        .clip(0, 100)
        .round(2)
    )

    # Calculate missing discounts
    missing_discount = (
        result["discount"] <= 0
    )

    if missing_discount.any():

        result.loc[
            missing_discount,
            "discount"
        ] = [
            calculate_discount(
                price,
                mrp
            )
            for price, mrp
            in zip(
                result.loc[
                    missing_discount,
                    "price"
                ],
                result.loc[
                    missing_discount,
                    "mrp"
                ]
            )
        ]

    # If INR price is missing, use price
    missing_inr = (
        result["price_inr"] <= 0
    )

    result.loc[
        missing_inr,
        "price_inr"
    ] = result.loc[
        missing_inr,
        "price"
    ]

    # If MRP is missing, use price
    missing_mrp = (
        result["mrp"] <= 0
    )

    result.loc[
        missing_mrp,
        "mrp"
    ] = result.loc[
        missing_mrp,
        "price"
    ]

    # Marketplace
    result["marketplace"] = (
        marketplace
    )

    # Remove products without names
    result = result[
        result[
            "product_name"
        ].str.strip() != ""
    ].copy()

    # Ensure product IDs
    result = ensure_ids(
        result,
        marketplace
    )

    return result[
        FINAL_COLUMNS
    ]


# ============================================================
# AMAZON
# ============================================================

def load_amazon():

    print()
    print(
        "Loading Amazon electronics dataset..."
    )

    df = safe_read_csv(
        AMAZON_FILE
    )

    if df.empty:

        return pd.DataFrame(
            columns=FINAL_COLUMNS
        )

    print(
        f"Amazon source rows: {len(df):,}"
    )

    result = pd.DataFrame(
        index=df.index
    )

    result["marketplace"] = (
        "amazon"
    )

    # --------------------------------------------------------
    # Amazon link
    # --------------------------------------------------------

    links = get_text_column(
        df,
        [
            "link",
            "product_url",
            "url"
        ]
    )

    # --------------------------------------------------------
    # Amazon product ID / ASIN
    # --------------------------------------------------------

    def amazon_id(
        link,
        index
    ):

        link = clean_text(
            link
        )

        patterns = [
            r"/dp/([A-Za-z0-9]{8,12})",
            r"/gp/product/([A-Za-z0-9]{8,12})",
            r"/product/([A-Za-z0-9]{8,12})",
        ]

        for pattern in patterns:

            match = re.search(
                pattern,
                link
            )

            if match:

                return match.group(
                    1
                ).upper()

        return make_fallback_id(
            "amazon",
            index
        )

    result["product_id"] = [
        amazon_id(
            link,
            index
        )
        for index, link
        in enumerate(links)
    ]

    # --------------------------------------------------------
    # Product name
    # --------------------------------------------------------

    result["product_name"] = (
        get_text_column(
            df,
            [
                "name",
                "product_name",
                "Name"
            ]
        )
    )

    # --------------------------------------------------------
    # Brand
    # --------------------------------------------------------

    # The new Amazon dataset does not have a dedicated
    # brand column. Derive a simple brand from the name.
    def derive_brand(name):

        name = clean_text(
            name
        )

        if not name:
            return ""

        return name.split()[0]

    result["brand"] = (
        result["product_name"]
        .apply(derive_brand)
    )

    # --------------------------------------------------------
    # Category
    # --------------------------------------------------------

    main_category = (
        get_text_column(
            df,
            [
                "main_category",
                "category",
                "Category"
            ]
        )
    )

    sub_category = (
        get_text_column(
            df,
            [
                "sub_category",
                "subcategory",
                "Sub Category"
            ]
        )
    )

    result["category"] = (
        main_category
        + " / "
        + sub_category
    ).str.strip(" /")

    # --------------------------------------------------------
    # Price
    # --------------------------------------------------------

    result["price"] = (
        get_number_column(
            df,
            [
                "discount_price",
                "discounted_price",
                "Selling Price",
                "price"
            ]
        )
    )

    # --------------------------------------------------------
    # Actual price / MRP
    # --------------------------------------------------------

    result["mrp"] = (
        get_number_column(
            df,
            [
                "actual_price",
                "MRP",
                "mrp"
            ]
        )
    )

    # --------------------------------------------------------
    # Discount
    # --------------------------------------------------------

    result["discount"] = [
        calculate_discount(
            price,
            mrp
        )
        for price, mrp
        in zip(
            result["price"],
            result["mrp"]
        )
    ]

    # --------------------------------------------------------
    # Rating
    # --------------------------------------------------------

    result["rating"] = (
        get_number_column(
            df,
            [
                "review_rating",
                "rating",
                "Ratings",
                "product_rating"
            ]
        )
        .apply(clean_rating)
    )

    # --------------------------------------------------------
    # Reviews
    # --------------------------------------------------------

    result["reviews"] = (
        get_number_column(
            df,
            [
                "no_of_ratings",
                "rating_count",
                "No_of_ratings",
                "reviews"
            ]
        )
    )

    # --------------------------------------------------------
    # Image
    # --------------------------------------------------------

    result["image"] = (
        get_text_column(
            df,
            [
                "image",
                "img_link",
                "image_url"
            ]
        )
        .apply(parse_list_first)
    )

    # --------------------------------------------------------
    # Product URL
    # --------------------------------------------------------

    result["product_url"] = (
        links
    )

    # --------------------------------------------------------
    # Currency / availability
    # --------------------------------------------------------

    result["currency"] = (
        "INR"
    )

    result["availability"] = (
        "Available"
    )

    result["original_currency"] = (
        "INR"
    )

    result["original_price"] = (
        result["price"]
    )

    result["price_inr"] = (
        result["price"]
    )

    result = normalize_result(
        result,
        "amazon"
    )

    print(
        f"Amazon rows loaded: {len(result):,}"
    )

    print(
        "Amazon images:",
        f"{int(result['image'].ne('').sum()):,}",
        "/",
        f"{len(result):,}"
    )

    print(
        "Amazon links:",
        f"{int(result['product_url'].ne('').sum()):,}",
        "/",
        f"{len(result):,}"
    )

    return result


# ============================================================
# FLIPKART
# ============================================================

def load_flipkart():

    print()
    print(
        "Loading Flipkart..."
    )

    df = safe_read_csv(
        FLIPKART_FILE
    )

    if df.empty:

        return pd.DataFrame(
            columns=FINAL_COLUMNS
        )

    print(
        f"Flipkart source rows: {len(df):,}"
    )

    result = pd.DataFrame(
        index=df.index
    )

    result["marketplace"] = (
        "flipkart"
    )

    # Product ID
    result["product_id"] = (
        get_text_column(
            df,
            [
                "pid",
                "product_id",
                "id",
                "uniq_id"
            ]
        )
    )

    # Product name
    result["product_name"] = (
        get_text_column(
            df,
            [
                "product_name",
                "Name",
                "name"
            ]
        )
    )

    # Brand
    result["brand"] = (
        get_text_column(
            df,
            [
                "brand",
                "Brand"
            ]
        )
    )

    # Category
    result["category"] = (
        get_text_column(
            df,
            [
                "product_category_tree",
                "Category",
                "category"
            ]
        )
    )

    # Price
    result["price"] = (
        get_number_column(
            df,
            [
                "discounted_price",
                "Selling Price",
                "price"
            ]
        )
    )

    # MRP
    result["mrp"] = (
        get_number_column(
            df,
            [
                "retail_price",
                "MRP",
                "mrp"
            ]
        )
    )

    # Discount
    result["discount"] = [
        calculate_discount(
            price,
            mrp
        )
        for price, mrp
        in zip(
            result["price"],
            result["mrp"]
        )
    ]

    # Rating
    result["rating"] = (
        get_number_column(
            df,
            [
                "product_rating",
                "overall_rating",
                "Ratings",
                "rating"
            ]
        )
        .apply(clean_rating)
    )

    # Reviews
    result["reviews"] = (
        get_number_column(
            df,
            [
                "review_count",
                "reviews",
                "rating_count"
            ]
        )
    )

    # Image
    result["image"] = (
        get_text_column(
            df,
            [
                "image",
                "img_link",
                "image_url"
            ]
        )
        .apply(parse_list_first)
    )

    # URL
    result["product_url"] = (
        get_text_column(
            df,
            [
                "product_url",
                "product_link",
                "url"
            ]
        )
    )

    result["availability"] = (
        "Available"
    )

    result["currency"] = (
        "INR"
    )

    result["original_currency"] = (
        "INR"
    )

    result["original_price"] = (
        result["price"]
    )

    result["price_inr"] = (
        result["price"]
    )

    result = normalize_result(
        result,
        "flipkart"
    )

    print(
        f"Flipkart rows loaded: {len(result):,}"
    )

    return result


# ============================================================
# WALMART
# ============================================================

def load_walmart():

    print()
    print(
        "Loading Walmart..."
    )

    df = safe_read_csv(
        WALMART_FILE
    )

    if df.empty:

        return pd.DataFrame(
            columns=FINAL_COLUMNS
        )

    print(
        f"Walmart source rows: {len(df):,}"
    )

    result = pd.DataFrame(
        index=df.index
    )

    result["marketplace"] = (
        "walmart"
    )

    # Product ID
    result["product_id"] = (
        get_text_column(
            df,
            [
                "product_id",
                "id",
                "sku"
            ]
        )
    )

    # Product name
    result["product_name"] = (
        get_text_column(
            df,
            [
                "product_name",
                "name",
                "title",
                "Name"
            ]
        )
    )

    # Brand
    result["brand"] = (
        get_text_column(
            df,
            [
                "brand",
                "Brand",
                "manufacturer"
            ]
        )
    )

    # Category
    category_name = (
        get_text_column(
            df,
            [
                "category_name",
                "category",
                "Category",
                "product_category"
            ]
        )
    )

    category_path = (
        get_text_column(
            df,
            [
                "category_path",
                "categories",
                "category_tree"
            ]
        )
    )

    result["category"] = (
        category_name
        + " / "
        + category_path
    ).str.strip(" /")

    # Price
    result["price"] = (
        get_number_column(
            df,
            [
                "final_price",
                "price",
                "sale_price",
                "selling_price",
                "Selling Price"
            ]
        )
    )

    # MRP
    result["mrp"] = (
        get_number_column(
            df,
            [
                "initial_price",
                "mrp",
                "regular_price",
                "retail_price",
                "MRP"
            ]
        )
    )

    # Discount
    result["discount"] = (
        get_number_column(
            df,
            [
                "discount",
                "discount_percentage"
            ]
        )
    )

    # Rating
    result["rating"] = (
        get_number_column(
            df,
            [
                "rating",
                "rating_stars",
                "ratings",
                "customer_rating"
            ]
        )
        .apply(clean_rating)
    )

    # Reviews
    result["reviews"] = (
        get_number_column(
            df,
            [
                "review_count",
                "reviews",
                "rating_count"
            ]
        )
    )

    # Images
    result["image"] = (
        get_text_column(
            df,
            [
                "main_image",
                "image",
                "image_url",
                "image_urls",
                "img_link"
            ]
        )
        .apply(parse_list_first)
    )

    # URL
    result["product_url"] = (
        get_text_column(
            df,
            [
                "url",
                "product_url",
                "product_link"
            ]
        )
    )

    # Availability
    delivery = (
        get_text_column(
            df,
            [
                "available_for_delivery"
            ]
        )
    )

    pickup = (
        get_text_column(
            df,
            [
                "available_for_pickup"
            ]
        )
    )

    def walmart_availability(
        row
    ):

        delivery_value = (
            clean_text(
                row["delivery"]
            )
            .lower()
        )

        pickup_value = (
            clean_text(
                row["pickup"]
            )
            .lower()
        )

        if (
            delivery_value
            in {
                "true",
                "1",
                "yes"
            }
            or
            pickup_value
            in {
                "true",
                "1",
                "yes"
            }
        ):

            return "Available"

        if (
            delivery_value
            in {
                "false",
                "0",
                "no"
            }
            and
            pickup_value
            in {
                "false",
                "0",
                "no"
            }
        ):

            return "Unavailable"

        return "Available"

    availability_df = pd.DataFrame(
        {
            "delivery": delivery,
            "pickup": pickup
        },
        index=df.index
    )

    result["availability"] = (
        availability_df
        .apply(
            walmart_availability,
            axis=1
        )
    )

    # Walmart source is treated as USD
    result["original_currency"] = (
        "USD"
    )

    result["original_price"] = (
        result["price"]
    )

    result["price_inr"] = (
        result["price"]
        * USD_TO_INR
    )

    result["price"] = (
        result["price_inr"]
    )

    result["mrp"] = (
        result["mrp"]
        * USD_TO_INR
    )

    result["currency"] = (
        "INR"
    )

    # Calculate missing discount
    result["discount"] = [
        discount
        if discount > 0
        else calculate_discount(
            price,
            mrp
        )
        for price, mrp, discount
        in zip(
            result["price"],
            result["mrp"],
            result["discount"]
        )
    ]

    result = normalize_result(
        result,
        "walmart"
    )

    print(
        f"Walmart rows loaded: {len(result):,}"
    )

    return result


# ============================================================
# BEST BUY
# ============================================================

def load_bestbuy():

    print()
    print(
        "Loading Best Buy..."
    )

    df = safe_read_csv(
        BESTBUY_FILE
    )

    if df.empty:

        return pd.DataFrame(
            columns=FINAL_COLUMNS
        )

    print(
        f"Best Buy source rows: {len(df):,}"
    )

    result = pd.DataFrame(
        index=df.index
    )

    result["marketplace"] = (
        "bestbuy"
    )

    # Product ID
    result["product_id"] = (
        get_text_column(
            df,
            [
                "product_id",
                "sku",
                "id"
            ]
        )
    )

    # Product name
    result["product_name"] = (
        get_text_column(
            df,
            [
                "product_name",
                "product-display-name",
                "name",
                "title"
            ]
        )
    )

    # Brand
    result["brand"] = (
        get_text_column(
            df,
            [
                "brand",
                "manufacturer"
            ]
        )
    )

    # Category
    result["category"] = (
        get_text_column(
            df,
            [
                "category",
                "product-category",
                "product_category"
            ]
        )
    )

    # Price
    result["price"] = (
        get_number_column(
            df,
            [
                "price",
                "salePrice",
                "selling_price"
            ]
        )
    )

    # MRP
    result["mrp"] = (
        get_number_column(
            df,
            [
                "mrp",
                "regularPrice",
                "retail_price"
            ]
        )
    )

    # Discount
    result["discount"] = (
        get_number_column(
            df,
            [
                "discount",
                "discount_percentage"
            ]
        )
    )

    # Rating
    result["rating"] = (
        get_number_column(
            df,
            [
                "rating",
                "customerReviewAverage",
                "product_rating"
            ]
        )
        .apply(clean_rating)
    )

    # Reviews
    result["reviews"] = (
        get_number_column(
            df,
            [
                "reviews",
                "customerReviewCount",
                "review_count"
            ]
        )
    )

    # Image
    result["image"] = (
        get_text_column(
            df,
            [
                "image",
                "image-uri",
                "image_url",
                "img_link"
            ]
        )
        .apply(parse_list_first)
    )

    # URL
    result["product_url"] = (
        get_text_column(
            df,
            [
                "product_url",
                "url",
                "product-link"
            ]
        )
    )

    # Availability
    result["availability"] = (
        get_text_column(
            df,
            [
                "availability",
                "stock",
                "availability_status"
            ]
        )
        .apply(parse_availability)
    )

    # Best Buy source is treated as USD
    result["original_currency"] = (
        "USD"
    )

    result["original_price"] = (
        result["price"]
    )

    result["price_inr"] = (
        result["price"]
        * USD_TO_INR
    )

    result["price"] = (
        result["price_inr"]
    )

    result["mrp"] = (
        result["mrp"]
        * USD_TO_INR
    )

    result["currency"] = (
        "INR"
    )

    # Calculate missing discount
    result["discount"] = [
        discount
        if discount > 0
        else calculate_discount(
            price,
            mrp
        )
        for price, mrp, discount
        in zip(
            result["price"],
            result["mrp"],
            result["discount"]
        )
    ]

    result = normalize_result(
        result,
        "bestbuy"
    )

    print(
        f"Best Buy rows loaded: {len(result):,}"
    )

    return result


# ============================================================
# MAIN DATA PREPARATION
# ============================================================

def main():

    print()
    print("=" * 72)
    print(
        "CREATING FINAL MARKETPLACE DATASET"
    )
    print(
        "Amazon + Flipkart + Walmart + Best Buy"
    )
    print("=" * 72)

    # --------------------------------------------------------
    # Check dataset folder
    # --------------------------------------------------------

    if not os.path.exists(
        DATASET_DIR
    ):

        print()
        print(
            "ERROR: Dataset folder not found:"
        )

        print(
            DATASET_DIR
        )

        print()
        print(
            "Please make sure the folder exists:"
        )

        print(
            os.path.join(
                BASE_DIR,
                "dataset"
            )
        )

        return

    # --------------------------------------------------------
    # Show paths being used
    # --------------------------------------------------------

    print()
    print(
        "Project folder:"
    )
    print(
        BASE_DIR
    )

    print()
    print(
        "Dataset folder:"
    )
    print(
        DATASET_DIR
    )

    # --------------------------------------------------------
    # Load marketplaces
    # --------------------------------------------------------

    amazon = load_amazon()

    flipkart = load_flipkart()

    walmart = load_walmart()

    bestbuy = load_bestbuy()

    # --------------------------------------------------------
    # Combine datasets
    #
    # Required order:
    # Amazon
    # Flipkart
    # Walmart
    # Best Buy
    # --------------------------------------------------------

    combined = pd.concat(
        [
            amazon,
            flipkart,
            walmart,
            bestbuy
        ],
        ignore_index=True
    )

    # --------------------------------------------------------
    # Make sure all columns exist
    # --------------------------------------------------------

    for column in FINAL_COLUMNS:

        if column not in combined.columns:

            combined[column] = ""

    combined = combined[
        FINAL_COLUMNS
    ].copy()

    # --------------------------------------------------------
    # Clean text columns
    # --------------------------------------------------------

    text_columns = [
        "marketplace",
        "product_id",
        "product_name",
        "brand",
        "category",
        "currency",
        "image",
        "product_url",
        "availability",
        "original_currency",
    ]

    for column in text_columns:

        combined[column] = (
            combined[column]
            .apply(clean_text)
        )

    # --------------------------------------------------------
    # Force numeric columns
    # --------------------------------------------------------

    numeric_columns = [
        "price",
        "mrp",
        "discount",
        "rating",
        "reviews",
        "original_price",
        "price_inr",
    ]

    for column in numeric_columns:

        combined[column] = pd.to_numeric(
            combined[column],
            errors="coerce"
        ).fillna(0.0)

    # --------------------------------------------------------
    # Numeric cleanup
    # --------------------------------------------------------

    combined["price"] = (
        combined["price"]
        .clip(lower=0)
        .round(2)
    )

    combined["mrp"] = (
        combined["mrp"]
        .clip(lower=0)
        .round(2)
    )

    combined["rating"] = (
        combined["rating"]
        .clip(0, 5)
        .round(2)
    )

    combined["reviews"] = (
        combined["reviews"]
        .clip(lower=0)
        .round(0)
    )

    combined["discount"] = (
        combined["discount"]
        .clip(0, 100)
        .round(2)
    )

    combined["price_inr"] = (
        combined["price_inr"]
        .clip(lower=0)
        .round(2)
    )

    combined["original_price"] = (
        combined["original_price"]
        .clip(lower=0)
        .round(2)
    )

    # --------------------------------------------------------
    # Calculate discounts where missing
    # --------------------------------------------------------

    missing_discount = (
        combined["discount"] <= 0
    )

    if missing_discount.any():

        calculated_discounts = []

        for price, mrp in zip(
            combined.loc[
                missing_discount,
                "price"
            ],
            combined.loc[
                missing_discount,
                "mrp"
            ]
        ):

            calculated_discounts.append(
                calculate_discount(
                    price,
                    mrp
                )
            )

        combined.loc[
            missing_discount,
            "discount"
        ] = calculated_discounts

    # --------------------------------------------------------
    # Missing INR price
    # --------------------------------------------------------

    missing_price_inr = (
        combined["price_inr"] <= 0
    )

    combined.loc[
        missing_price_inr,
        "price_inr"
    ] = combined.loc[
        missing_price_inr,
        "price"
    ]

    # --------------------------------------------------------
    # Missing MRP
    # --------------------------------------------------------

    missing_mrp = (
        combined["mrp"] <= 0
    )

    combined.loc[
        missing_mrp,
        "mrp"
    ] = combined.loc[
        missing_mrp,
        "price"
    ]

    # --------------------------------------------------------
    # Remove products with no name
    # --------------------------------------------------------

    combined = combined[
        combined[
            "product_name"
        ].str.strip() != ""
    ].copy()

    # --------------------------------------------------------
    # Ensure IDs
    # --------------------------------------------------------

    for index in combined.index:

        if not combined.at[
            index,
            "product_id"
        ]:

            marketplace = (
                combined.at[
                    index,
                    "marketplace"
                ]
            )

            if not marketplace:
                marketplace = "product"

            combined.at[
                index,
                "product_id"
            ] = make_fallback_id(
                marketplace,
                index
            )

    # --------------------------------------------------------
    # Remove duplicate marketplace + product ID
    # --------------------------------------------------------

    before_duplicates = (
        len(combined)
    )

    combined = (
        combined
        .drop_duplicates(
            subset=[
                "marketplace",
                "product_id"
            ],
            keep="first"
        )
        .copy()
    )

    duplicates_removed = (
        before_duplicates
        - len(combined)
    )

    # --------------------------------------------------------
    # Fixed marketplace order
    # --------------------------------------------------------

    marketplace_order = [
        "amazon",
        "flipkart",
        "walmart",
        "bestbuy"
    ]

    combined["marketplace"] = pd.Categorical(
        combined["marketplace"],
        categories=marketplace_order,
        ordered=True
    )

    combined = (
        combined
        .sort_values(
            by="marketplace",
            kind="stable"
        )
        .reset_index(
            drop=True
        )
    )

    combined["marketplace"] = (
        combined["marketplace"]
        .astype(str)
    )

    # --------------------------------------------------------
    # Final numeric conversion
    # --------------------------------------------------------

    for column in numeric_columns:

        combined[column] = pd.to_numeric(
            combined[column],
            errors="coerce"
        ).fillna(0.0)

    # --------------------------------------------------------
    # Save CSV
    # --------------------------------------------------------

    combined.to_csv(
        OUTPUT_FILE,
        index=False,
        encoding="utf-8-sig"
    )

    # ========================================================
    # FINAL VALIDATION
    # ========================================================

    print()
    print("=" * 72)
    print(
        "FINAL VALIDATION"
    )
    print("=" * 72)

    print()
    print(
        f"Total products: {len(combined):,}"
    )

    print(
        "Duplicate marketplace/product IDs removed:",
        f"{duplicates_removed:,}"
    )

    # --------------------------------------------------------
    # Marketplace counts
    # --------------------------------------------------------

    print()
    print(
        "Marketplace counts:"
    )

    counts = (
        combined[
            "marketplace"
        ]
        .value_counts()
    )

    for marketplace in marketplace_order:

        print(
            f"  {marketplace:10s}: "
            f"{int(counts.get(marketplace, 0)):,}"
        )

    # --------------------------------------------------------
    # Images
    # --------------------------------------------------------

    image_count = int(
        combined[
            "image"
        ]
        .ne("")
        .sum()
    )

    print()
    print(
        "Images:"
    )

    print(
        f"  With image:    {image_count:,}"
    )

    print(
        f"  Without image: "
        f"{len(combined) - image_count:,}"
    )

    # --------------------------------------------------------
    # Product links
    # --------------------------------------------------------

    link_count = int(
        combined[
            "product_url"
        ]
        .ne("")
        .sum()
    )

    print()
    print(
        "Product links:"
    )

    print(
        f"  With link:     {link_count:,}"
    )

    print(
        f"  Without link:  "
        f"{len(combined) - link_count:,}"
    )

    # --------------------------------------------------------
    # Price validation
    # --------------------------------------------------------

    price_count = int(
        (
            combined["price_inr"]
            > 0
        ).sum()
    )

    print()
    print(
        "Prices:"
    )

    print(
        f"  With price:    {price_count:,}"
    )

    print(
        f"  Without price: "
        f"{len(combined) - price_count:,}"
    )

    # --------------------------------------------------------
    # Output file
    # --------------------------------------------------------

    print()
    print(
        "Output file:"
    )

    print(
        OUTPUT_FILE
    )

    # --------------------------------------------------------
    # Preview
    # --------------------------------------------------------

    print()
    print(
        "First 10 products:"
    )

    preview_columns = [
        "marketplace",
        "product_id",
        "product_name",
        "price_inr",
        "rating",
        "discount"
    ]

    print(
        combined[
            preview_columns
        ]
        .head(10)
        .to_string(
            index=False
        )
    )

    # --------------------------------------------------------
    # Amazon verification
    # --------------------------------------------------------

    amazon_rows = combined[
        combined["marketplace"]
        == "amazon"
    ]

    print()
    print(
        "Amazon verification:"
    )

    print(
        f"  Products: "
        f"{len(amazon_rows):,}"
    )

    print(
        f"  Images:   "
        f"{int(amazon_rows['image'].ne('').sum()):,}"
    )

    print(
        f"  Links:    "
        f"{int(amazon_rows['product_url'].ne('').sum()):,}"
    )

    print()
    print("=" * 72)
    print(
        "FINAL DATASET CREATED SUCCESSFULLY"
    )
    print("=" * 72)


# ============================================================
# START PROGRAM
# ============================================================

if __name__ == "__main__":

    main()