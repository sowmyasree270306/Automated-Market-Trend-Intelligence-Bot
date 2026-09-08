import sqlite3


DATABASE = "database.db"


# ==========================================
# FRUIT VARIETY RULES
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
    ]
}


# ==========================================
# CONNECT DATABASE
# ==========================================

conn = sqlite3.connect(DATABASE)

cursor = conn.cursor()


print()
print("=" * 60)
print("FIXING FRUIT PRODUCTS")
print("=" * 60)
print()


# ==========================================
# CHECK CURRENT FRUIT PRODUCTS
# ==========================================

cursor.execute(
    """
    SELECT id, title
    FROM api_products
    WHERE LOWER(category) = 'groceries'
    ORDER BY id
    """
)

products = cursor.fetchall()


print(
    f"Total grocery products found: {len(products)}"
)

print()


# ==========================================
# PROCESS FRUITS
# ==========================================

updated = 0

deleted = 0


for product_id, title in products:

    original_title = title

    title_lower = title.lower()


    detected_fruit = None


    for fruit in FRUIT_VARIANTS:

        if fruit in title_lower:

            detected_fruit = fruit

            break


    if detected_fruit is None:

        continue


    # ======================================
    # REMOVE OLD FRUIT VARIANTS
    # ======================================

    # If title is already one of our correct
    # two varieties, keep it.
    # ======================================

    correct_variants = FRUIT_VARIANTS[
        detected_fruit
    ]


    already_correct = False


    for variant in correct_variants:

        if title_lower.endswith(
            variant.lower()
        ):

            already_correct = True

            break


    if already_correct:

        continue


    # ======================================
    # ORIGINAL FRUIT
    # ======================================

    # Example:
    #
    # Apple
    # Strawberry
    #
    # These are replaced by the first
    # variety.
    # ======================================

    if title_lower.strip() == detected_fruit:

        new_title = (
            f"{detected_fruit.title()} "
            f"{correct_variants[0]}"
        )


        cursor.execute(
            """
            UPDATE api_products

            SET title = ?

            WHERE id = ?
            """,

            (
                new_title,
                product_id
            )
        )


        updated += 1

        print(
            f"Updated: {original_title} "
            f"-> {new_title}"
        )

        continue


    # ======================================
    # REMOVE PHONE-STYLE FRUIT VARIANTS
    # ======================================

    phone_words = [

        "standard",

        "premium",

        "plus",

        "pro",

        "max",

        "lite",

        "advanced",

        "special edition",

        "64gb",

        "128gb",

        "256gb",

        "512gb",

        "1tb",

        "black",

        "white",

        "blue",

        "green",

        "red",

        "silver",

        "gold"

    ]


    # If an old generated variant exists,
    # replace it with a proper fruit variety.

    generated_variant = False


    for word in phone_words:

        if word in title_lower:

            generated_variant = True

            break


    if generated_variant:

        base_title = original_title


        for word in phone_words:

            base_title = base_title.replace(
                word,
                ""
            )


            base_title = base_title.replace(
                word.title(),
                ""
            )


            base_title = base_title.replace(
                word.upper(),
                ""
            )


        base_title = " ".join(
            base_title.split()
        ).strip()


        # Remove trailing spaces/symbols

        base_title = base_title.rstrip(
            "- ,"
        )


        new_title = (
            f"{base_title} "
            f"{correct_variants[0]}"
        )


        cursor.execute(
            """
            UPDATE api_products

            SET title = ?

            WHERE id = ?
            """,

            (
                new_title,
                product_id
            )
        )


        updated += 1


# ==========================================
# CREATE EXACT SECOND VARIANTS
# ==========================================

for fruit, variants in FRUIT_VARIANTS.items():

    # Find the current products for this fruit

    cursor.execute(
        """
        SELECT
            id,
            title,
            price,
            rating,
            discount_percentage,
            stock,
            brand,
            category,
            thumbnail
        FROM api_products

        WHERE LOWER(category) = 'groceries'

        AND LOWER(title) LIKE ?
        """,

        (
            f"%{fruit}%",

        )
    )


    fruit_products = cursor.fetchall()


    if not fruit_products:

        continue


    # Find the first product as the base

    base = fruit_products[0]


    base_id = base[0]

    base_title = base[1]

    price = base[2]

    rating = base[3]

    discount = base[4]

    stock = base[5]

    brand = base[6]

    category = base[7]

    thumbnail = base[8]


    # ======================================
    # ENSURE FIRST VARIETY
    # ======================================

    first_title = (
        f"{fruit.title()} "
        f"{variants[0]}"
    )


    cursor.execute(
        """
        UPDATE api_products

        SET title = ?

        WHERE id = ?
        """,

        (
            first_title,
            base_id
        )
    )


    # ======================================
    # CHECK SECOND VARIETY
    # ======================================

    second_title = (
        f"{fruit.title()} "
        f"{variants[1]}"
    )


    cursor.execute(
        """
        SELECT id
        FROM api_products

        WHERE LOWER(title) = LOWER(?)

        LIMIT 1
        """,

        (
            second_title,
        )
    )


    existing_second = cursor.fetchone()


    if existing_second:

        continue


    # ======================================
    # FIND AN OLD DUPLICATE FRUIT PRODUCT
    # ======================================

    cursor.execute(
        """
        SELECT id
        FROM api_products

        WHERE LOWER(category) = 'groceries'

        AND LOWER(title) LIKE ?

        AND id != ?

        LIMIT 1
        """,

        (
            f"%{fruit}%",

            base_id
        )
    )


    second_product = cursor.fetchone()


    if second_product:

        second_id = second_product[0]


        cursor.execute(
            """
            UPDATE api_products

            SET title = ?

            WHERE id = ?
            """,

            (
                second_title,
                second_id
            )
        )


    else:

        # No second product available.
        # We don't create extra rows because
        # the catalog must remain controlled.

        pass


# ==========================================
# SAVE
# ==========================================

conn.commit()


# ==========================================
# VERIFY
# ==========================================

print()

print("=" * 60)

print("FRUIT PRODUCTS AFTER FIX")

print("=" * 60)

print()


cursor.execute(
    """
    SELECT
        id,
        title,
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

    )

    ORDER BY title
    """
)


fruit_rows = cursor.fetchall()


for product_id, title, price in fruit_rows:

    print(
        f"{product_id} | "
        f"{title} | "
        f"₹{round(price * 85, 2)}"
    )


# ==========================================
# FINAL COUNT
# ==========================================

cursor.execute(
    """
    SELECT COUNT(*)
    FROM api_products
    """
)


total_products = cursor.fetchone()[0]


conn.close()


print()

print("=" * 60)

print(
    f"TOTAL PRODUCTS: {total_products}"
)

print("=" * 60)

print()

print(
    "Fruit cleanup completed."
)

print(
    "No API request was made."
)

print()