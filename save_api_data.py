import requests
import sqlite3
from datetime import datetime
import random


# ==========================================
# SETTINGS
# ==========================================

API_URL = "https://dummyjson.com/products?limit=0"

DATABASE = "database.db"

USD_TO_INR = 85

TARGET_PRODUCTS = 1000


random.seed(42)


# ==========================================
# FRUIT VARIETIES
# ==========================================

FRUIT_VARIANTS = {

    "apple": [
        "Green",
        "Red"
    ],

    "banana": [
        "Yellow",
        "Premium"
    ],

    "mango": [
        "Alphonso",
        "Kesar"
    ],

    "strawberry": [
        "Fresh",
        "Premium"
    ],

    "orange": [
        "Regular",
        "Premium"
    ],

    "watermelon": [
        "Seedless",
        "Regular"
    ],

    "pineapple": [
        "Fresh",
        "Premium"
    ],

    "grape": [
        "Green",
        "Black"
    ],

    "grapes": [
        "Green",
        "Black"
    ],

    "peach": [
        "Fresh",
        "Premium"
    ],

    "kiwi": [
        "Green",
        "Golden"
    ],

    "pear": [
        "Green",
        "Premium"
    ],

    "cherry": [
        "Fresh",
        "Premium"
    ],

    "papaya": [
        "Fresh",
        "Premium"
    ],

    "pomegranate": [
        "Regular",
        "Premium"
    ]
}


# ==========================================
# FRUIT KEYWORDS
# ==========================================

FRUIT_KEYWORDS = [
    "apple",
    "banana",
    "mango",
    "strawberry",
    "orange",
    "watermelon",
    "pineapple",
    "grape",
    "grapes",
    "peach",
    "kiwi",
    "pear",
    "cherry",
    "papaya",
    "pomegranate"
]


# ==========================================
# OTHER VARIANTS
# ==========================================

ELECTRONIC_VARIANTS = [
    "Standard",
    "Premium",
    "Plus",
    "Pro",
    "Max",
    "Lite",
    "Advanced",
    "Special Edition"
]


CLOTHING_VARIANTS = [
    "Regular",
    "Premium",
    "Classic",
    "Comfort",
    "Modern",
    "Deluxe"
]


GENERAL_VARIANTS = [
    "Standard",
    "Premium",
    "Classic",
    "Deluxe",
    "Special"
]


COLORS = [
    "Black",
    "White",
    "Blue",
    "Green",
    "Red",
    "Silver",
    "Gold"
]


STORAGE_OPTIONS = [
    "64GB",
    "128GB",
    "256GB",
    "512GB",
    "1TB"
]


# ==========================================
# DETECT FRUIT
# ==========================================

def detect_fruit(title):

    title_lower = title.lower()

    for fruit in FRUIT_KEYWORDS:

        if fruit in title_lower:
            return fruit

    return None


# ==========================================
# GET FRUIT VARIANTS
# ==========================================

def get_fruit_variants(title):

    fruit = detect_fruit(title)

    if fruit:

        return FRUIT_VARIANTS.get(
            fruit,
            ["Fresh", "Premium"]
        )

    return []


# ==========================================
# CREATE PRODUCT VARIANT
# ==========================================

def create_variant(product, variant_number):

    title = str(
        product.get(
            "title",
            "Product"
        )
    ).strip()


    category = str(
        product.get(
            "category",
            ""
        )
    ).strip().lower()


    price = float(
        product.get(
            "price",
            0
        ) or 0
    )


    rating = float(
        product.get(
            "rating",
            0
        ) or 0
    )


    discount = float(
        product.get(
            "discountPercentage",
            0
        ) or 0
    )


    stock = int(
        product.get(
            "stock",
            0
        ) or 0
    )


    brand = str(
        product.get(
            "brand",
            "Generic"
        )
        or "Generic"
    ).strip()


    thumbnail = str(
        product.get(
            "thumbnail",
            ""
        )
        or ""
    ).strip()


    # ======================================
    # FRUIT
    # ======================================

    fruit = detect_fruit(title)


    if category == "groceries" and fruit:

        variants = get_fruit_variants(title)

        selected_variant = variants[
            variant_number % len(variants)
        ]


        new_title = (
            f"{title} {selected_variant}"
        )


        return {

            "title": new_title,

            "price": round(
                price * random.uniform(
                    0.90,
                    1.10
                ),
                2
            ),

            "rating": round(
                min(
                    5.0,
                    max(
                        3.5,
                        rating +
                        random.uniform(
                            -0.15,
                            0.15
                        )
                    )
                ),
                2
            ),

            "discount_percentage": round(
                min(
                    50,
                    max(
                        0,
                        discount +
                        random.uniform(
                            -3,
                            3
                        )
                    )
                ),
                2
            ),

            "stock": max(
                0,
                stock +
                random.randint(
                    -20,
                    30
                )
            ),

            "brand": brand,

            "category": "groceries",

            "thumbnail": thumbnail
        }


    # ======================================
    # SMARTPHONES
    # ======================================

    if category == "smartphones":

        variant = ELECTRONIC_VARIANTS[
            variant_number %
            len(ELECTRONIC_VARIANTS)
        ]


        storage = STORAGE_OPTIONS[
            variant_number %
            len(STORAGE_OPTIONS)
        ]


        color = COLORS[
            variant_number %
            len(COLORS)
        ]


        new_title = (
            f"{title} "
            f"{variant} "
            f"{storage} "
            f"{color}"
        )


        return {

            "title": new_title,

            "price": round(
                price *
                random.uniform(
                    0.90,
                    1.15
                ),
                2
            ),

            "rating": round(
                min(
                    5.0,
                    max(
                        3.0,
                        rating +
                        random.uniform(
                            -0.10,
                            0.10
                        )
                    )
                ),
                2
            ),

            "discount_percentage": round(
                min(
                    60,
                    max(
                        0,
                        discount +
                        random.uniform(
                            -4,
                            4
                        )
                    )
                ),
                2
            ),

            "stock": max(
                0,
                stock +
                random.randint(
                    -25,
                    40
                )
            ),

            "brand": brand,

            "category": category,

            "thumbnail": thumbnail
        }


    # ======================================
    # TABLETS
    # ======================================

    if category == "tablets":

        variant = ELECTRONIC_VARIANTS[
            variant_number %
            len(ELECTRONIC_VARIANTS)
        ]


        storage = STORAGE_OPTIONS[
            variant_number %
            len(STORAGE_OPTIONS)
        ]


        color = COLORS[
            variant_number %
            len(COLORS)
        ]


        new_title = (
            f"{title} "
            f"{variant} "
            f"{storage} "
            f"{color}"
        )


        return {

            "title": new_title,

            "price": round(
                price *
                random.uniform(
                    0.90,
                    1.15
                ),
                2
            ),

            "rating": round(
                min(
                    5.0,
                    max(
                        3.0,
                        rating +
                        random.uniform(
                            -0.10,
                            0.10
                        )
                    )
                ),
                2
            ),

            "discount_percentage": round(
                min(
                    60,
                    max(
                        0,
                        discount +
                        random.uniform(
                            -4,
                            4
                        )
                    )
                ),
                2
            ),

            "stock": max(
                0,
                stock +
                random.randint(
                    -25,
                    40
                )
            ),

            "brand": brand,

            "category": category,

            "thumbnail": thumbnail
        }


    # ======================================
    # LAPTOPS
    # ======================================

    if category == "laptops":

        variant = ELECTRONIC_VARIANTS[
            variant_number %
            len(ELECTRONIC_VARIANTS)
        ]


        storage = STORAGE_OPTIONS[
            variant_number %
            len(STORAGE_OPTIONS)
        ]


        color = COLORS[
            variant_number %
            len(COLORS)
        ]


        new_title = (
            f"{title} "
            f"{variant} "
            f"{storage} "
            f"{color}"
        )


        return {

            "title": new_title,

            "price": round(
                price *
                random.uniform(
                    0.90,
                    1.20
                ),
                2
            ),

            "rating": round(
                min(
                    5.0,
                    max(
                        3.0,
                        rating +
                        random.uniform(
                            -0.10,
                            0.10
                        )
                    )
                ),
                2
            ),

            "discount_percentage": round(
                min(
                    60,
                    max(
                        0,
                        discount +
                        random.uniform(
                            -4,
                            4
                        )
                    )
                ),
                2
            ),

            "stock": max(
                0,
                stock +
                random.randint(
                    -20,
                    35
                )
            ),

            "brand": brand,

            "category": category,

            "thumbnail": thumbnail
        }


    # ======================================
    # MOBILE ACCESSORIES
    # ======================================

    if category == "mobile-accessories":

        variant = GENERAL_VARIANTS[
            variant_number %
            len(GENERAL_VARIANTS)
        ]


        color = COLORS[
            variant_number %
            len(COLORS)
        ]


        new_title = (
            f"{title} "
            f"{variant} "
            f"{color}"
        )


        return {

            "title": new_title,

            "price": round(
                price *
                random.uniform(
                    0.90,
                    1.15
                ),
                2
            ),

            "rating": round(
                min(
                    5.0,
                    max(
                        3.0,
                        rating +
                        random.uniform(
                            -0.15,
                            0.15
                        )
                    )
                ),
                2
            ),

            "discount_percentage": round(
                min(
                    60,
                    max(
                        0,
                        discount +
                        random.uniform(
                            -4,
                            4
                        )
                    )
                ),
                2
            ),

            "stock": max(
                0,
                stock +
                random.randint(
                    -20,
                    40
                )
            ),

            "brand": brand,

            "category": category,

            "thumbnail": thumbnail
        }


    # ======================================
    # CLOTHING
    # ======================================

    clothing_categories = [

        "mens-shirts",

        "tops",

        "womens-dresses",

        "womens-bags",

        "womens-shoes",

        "mens-shoes"

    ]


    if category in clothing_categories:

        variant = CLOTHING_VARIANTS[
            variant_number %
            len(CLOTHING_VARIANTS)
        ]


        color = COLORS[
            variant_number %
            len(COLORS)
        ]


        new_title = (
            f"{title} "
            f"{variant} "
            f"{color}"
        )


        return {

            "title": new_title,

            "price": round(
                price *
                random.uniform(
                    0.90,
                    1.15
                ),
                2
            ),

            "rating": round(
                min(
                    5.0,
                    max(
                        3.0,
                        rating +
                        random.uniform(
                            -0.15,
                            0.15
                        )
                    )
                ),
                2
            ),

            "discount_percentage": round(
                min(
                    70,
                    max(
                        0,
                        discount +
                        random.uniform(
                            -5,
                            5
                        )
                    )
                ),
                2
            ),

            "stock": max(
                0,
                stock +
                random.randint(
                    -20,
                    50
                )
            ),

            "brand": brand,

            "category": category,

            "thumbnail": thumbnail
        }


    # ======================================
    # WATCHES
    # ======================================

    watch_categories = [

        "mens-watches",

        "womens-watches"

    ]


    if category in watch_categories:

        variant = GENERAL_VARIANTS[
            variant_number %
            len(GENERAL_VARIANTS)
        ]


        color = COLORS[
            variant_number %
            len(COLORS)
        ]


        new_title = (
            f"{title} "
            f"{variant} "
            f"{color}"
        )


        return {

            "title": new_title,

            "price": round(
                price *
                random.uniform(
                    0.90,
                    1.20
                ),
                2
            ),

            "rating": round(
                min(
                    5.0,
                    max(
                        3.0,
                        rating +
                        random.uniform(
                            -0.12,
                            0.12
                        )
                    )
                ),
                2
            ),

            "discount_percentage": round(
                min(
                    65,
                    max(
                        0,
                        discount +
                        random.uniform(
                            -4,
                            4
                        )
                    )
                ),
                2
            ),

            "stock": max(
                0,
                stock +
                random.randint(
                    -15,
                    35
                )
            ),

            "brand": brand,

            "category": category,

            "thumbnail": thumbnail
        }


    # ======================================
    # GENERAL PRODUCTS
    # ======================================

    variant = GENERAL_VARIANTS[
        variant_number %
        len(GENERAL_VARIANTS)
    ]


    new_title = (
        f"{title} {variant}"
    )


    return {

        "title": new_title,

        "price": round(
            price *
            random.uniform(
                0.90,
                1.15
            ),
            2
        ),

        "rating": round(
            min(
                5.0,
                max(
                    3.0,
                    rating +
                    random.uniform(
                        -0.15,
                        0.15
                    )
                )
            ),
            2
        ),

        "discount_percentage": round(
            min(
                70,
                max(
                    0,
                    discount +
                    random.uniform(
                        -4,
                        4
                    )
                )
            ),
            2
        ),

        "stock": max(
            0,
            stock +
            random.randint(
                -20,
                40
            )
        ),

        "brand": brand,

        "category": category,

        "thumbnail": thumbnail
    }


# ==========================================
# FETCH API DATA
# ==========================================

print()
print("=" * 60)
print("DUMMYJSON PRODUCT API")
print("=" * 60)
print()


try:

    response = requests.get(
        API_URL,
        timeout=30
    )

    response.raise_for_status()

    data = response.json()

    api_products = data.get(
        "products",
        []
    )


    print(
        f"Direct external API products: "
        f"{len(api_products)}"
    )


except Exception as error:

    print()
    print(
        "ERROR: Could not fetch API data."
    )

    print(error)

    print()

    raise SystemExit


if not api_products:

    print()

    print(
        "ERROR: API returned no products."
    )

    print()

    raise SystemExit


# ==========================================
# BUILD PRODUCT CATALOG
# ==========================================

catalog = []


# ==========================================
# ADD ORIGINAL NON-FRUIT PRODUCTS
# ==========================================

for product in api_products:

    category = str(
        product.get(
            "category",
            ""
        )
    ).strip().lower()


    title = str(
        product.get(
            "title",
            ""
        )
    ).strip()


    # --------------------------------------
    # IMPORTANT
    # --------------------------------------
    # Original fruits are NOT added.
    #
    # Only their two varieties will be
    # created below.
    # --------------------------------------

    fruit = detect_fruit(title)


    if category == "groceries" and fruit:

        continue


    # --------------------------------------
    # ORIGINAL NON-FRUIT PRODUCT
    # --------------------------------------

    catalog.append({

        "title": title,

        "price": float(
            product.get(
                "price",
                0
            ) or 0
        ),

        "rating": float(
            product.get(
                "rating",
                0
            ) or 0
        ),

        "discount_percentage": float(
            product.get(
                "discountPercentage",
                0
            ) or 0
        ),

        "stock": int(
            product.get(
                "stock",
                0
            ) or 0
        ),

        "brand": str(
            product.get(
                "brand",
                "Generic"
            )
            or "Generic"
        ).strip(),

        "category": category,

        "thumbnail": str(
            product.get(
                "thumbnail",
                ""
            )
            or ""
        ).strip()
    })


# ==========================================
# CREATE VARIANTS
# ==========================================

variant_round = 0


for product in api_products:

    if len(catalog) >= TARGET_PRODUCTS:

        break


    title = str(
        product.get(
            "title",
            ""
        )
    ).strip()


    category = str(
        product.get(
            "category",
            ""
        )
    ).strip().lower()


    # ======================================
    # FRUITS
    # ======================================

    fruit = detect_fruit(title)


    if category == "groceries" and fruit:

        fruit_variants = get_fruit_variants(
            title
        )


        # ----------------------------------
        # EXACTLY TWO VARIETIES
        # ----------------------------------

        for fruit_variant_index in range(2):

            if len(catalog) >= TARGET_PRODUCTS:

                break


            variant = create_variant(
                product,
                fruit_variant_index
            )


            # Avoid duplicate fruit names

            existing_titles = {

                item["title"]
                for item in catalog

            }


            if variant["title"] not in existing_titles:

                catalog.append(
                    variant
                )


        continue


    # ======================================
    # OTHER PRODUCTS
    # ======================================

    variant = create_variant(
        product,
        variant_round
    )


    catalog.append(
        variant
    )


    variant_round += 1


# ==========================================
# ADD MORE NON-FRUIT VARIANTS IF NEEDED
# ==========================================

while len(catalog) < TARGET_PRODUCTS:

    for product in api_products:

        if len(catalog) >= TARGET_PRODUCTS:

            break


        title = str(
            product.get(
                "title",
                ""
            )
        ).strip()


        category = str(
            product.get(
                "category",
                ""
            )
        ).strip().lower()


        fruit = detect_fruit(title)


        # ----------------------------------
        # SKIP FRUITS
        # ----------------------------------

        if category == "groceries" and fruit:

            continue


        variant = create_variant(
            product,
            variant_round
        )


        catalog.append(
            variant
        )


        variant_round += 1


# ==========================================
# EXACTLY 1000 PRODUCTS
# ==========================================

catalog = catalog[
    :TARGET_PRODUCTS
]


# ==========================================
# CONNECT SQLITE
# ==========================================

conn = sqlite3.connect(
    DATABASE
)


cursor = conn.cursor()


# ==========================================
# CREATE API PRODUCTS TABLE
# ==========================================

cursor.execute(
    """
    CREATE TABLE IF NOT EXISTS api_products (

        id INTEGER PRIMARY KEY,

        title TEXT,

        price REAL,

        rating REAL,

        discount_percentage REAL,

        stock INTEGER,

        brand TEXT,

        category TEXT,

        thumbnail TEXT,

        updated_at TEXT

    )
    """
)


# ==========================================
# CREATE HISTORY TABLE
# ==========================================

cursor.execute(
    """
    CREATE TABLE IF NOT EXISTS api_product_history (

        history_id INTEGER PRIMARY KEY AUTOINCREMENT,

        product_id INTEGER,

        title TEXT,

        price REAL,

        discount REAL,

        rating REAL,

        stock INTEGER,

        category TEXT,

        brand TEXT,

        api_date TEXT

    )
    """
)


# ==========================================
# DELETE OLD API PRODUCTS
# ==========================================

cursor.execute(
    "DELETE FROM api_products"
)


# ==========================================
# INSERT PRODUCTS
# ==========================================

current_time = datetime.now().strftime(
    "%Y-%m-%d %H:%M:%S"
)


for index, product in enumerate(
    catalog,
    start=1
):

    cursor.execute(
        """
        INSERT INTO api_products
        (
            id,
            title,
            price,
            rating,
            discount_percentage,
            stock,
            brand,
            category,
            thumbnail,
            updated_at
        )

        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,

        (
            index,

            product["title"],

            product["price"],

            product["rating"],

            product[
                "discount_percentage"
            ],

            product["stock"],

            product["brand"],

            product["category"],

            product["thumbnail"],

            current_time
        )
    )


# ==========================================
# COMMIT
# ==========================================

conn.commit()


# ==========================================
# CHECK PRODUCT COUNT
# ==========================================

cursor.execute(
    """
    SELECT COUNT(*)
    FROM api_products
    """
)


database_count = cursor.fetchone()[0]


# ==========================================
# CATEGORY SUMMARY
# ==========================================

cursor.execute(
    """
    SELECT
        category,
        COUNT(*)
    FROM api_products
    GROUP BY category
    ORDER BY COUNT(*) DESC
    """
)


category_rows = cursor.fetchall()


# ==========================================
# FRUIT PRODUCT CHECK
# ==========================================

cursor.execute(
    """
    SELECT
        id,
        title,
        category,
        price
    FROM api_products

    WHERE LOWER(category) = 'groceries'

    AND (

        LOWER(title) LIKE '%apple%'

        OR LOWER(title) LIKE '%banana%'

        OR LOWER(title) LIKE '%mango%'

        OR LOWER(title) LIKE '%strawberry%'

        OR LOWER(title) LIKE '%orange%'

        OR LOWER(title) LIKE '%watermelon%'

        OR LOWER(title) LIKE '%pineapple%'

        OR LOWER(title) LIKE '%grape%'

        OR LOWER(title) LIKE '%grapes%'

    )

    ORDER BY title

    LIMIT 30
    """
)


fruit_rows = cursor.fetchall()


# ==========================================
# CLOSE DATABASE
# ==========================================

conn.close()


# ==========================================
# OUTPUT
# ==========================================

print()

print("=" * 60)

print(
    "API DATA SAVING COMPLETED"
)

print("=" * 60)

print()


print(
    f"Direct external API products : "
    f"{len(api_products)}"
)


print(
    f"Expanded catalog products     : "
    f"{len(catalog)}"
)


print(
    f"Stored in SQLite              : "
    f"{database_count}"
)


# ==========================================
# CATEGORY SUMMARY
# ==========================================

print()

print("-" * 60)

print(
    "CATEGORY SUMMARY"
)

print("-" * 60)


for category, count in category_rows:

    print(
        f"{str(category):25} : {count}"
    )


# ==========================================
# FRUIT PREVIEW
# ==========================================

print()

print("-" * 60)

print(
    "FRUIT PRODUCT PREVIEW"
)

print("-" * 60)


for row in fruit_rows:

    product_id, title, category, price = row

    print(
        f"{title} | "
        f"₹{round(price * USD_TO_INR, 2)}"
    )


# ==========================================
# FINAL MESSAGE
# ==========================================

print()

print("=" * 60)

print("IMPORTANT")

print("=" * 60)

print()

print(
    "Fruit products use exactly two varieties."
)

print(
    "Original fruit products are not stored."
)

print(
    "No GB/TB/Pro/Max/Plus variants are used for fruits."
)

print()

print(
    "External API products are fetched from DummyJSON."
)

print(
    "The expanded catalog is generated locally "
    "for analytics and Product Explorer."
)

print()

print("=" * 60)