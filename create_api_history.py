import sqlite3
import random
from datetime import datetime, timedelta


# ============================================================
# CONFIGURATION
# ============================================================

DB_NAME = "database.db"

NUMBER_OF_DAYS = 30


# ============================================================
# CREATE HISTORICAL API DATA
# ============================================================

def create_historical_data():

    print("=" * 60)
    print("CREATING HISTORICAL API DATA")
    print("=" * 60)

    # --------------------------------------------------------
    # Connect to database
    # --------------------------------------------------------

    conn = sqlite3.connect(DB_NAME)

    cursor = conn.cursor()

    print("Database connected.")

    # --------------------------------------------------------
    # Check API products
    # --------------------------------------------------------

    cursor.execute("""
        SELECT
            id,
            title,
            price,
            rating,
            discount_percentage,
            stock,
            category,
            brand
        FROM api_products
        ORDER BY id
    """)

    products = cursor.fetchall()

    print(f"Products available in API catalog: {len(products)}")

    if len(products) == 0:

        print()
        print("ERROR: No products found in api_products.")
        print("Please run save_api_data.py first.")
        conn.close()
        return

    # --------------------------------------------------------
    # Create historical table
    # --------------------------------------------------------

    cursor.execute("""
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
    """)

    print("Historical table ready.")

    # --------------------------------------------------------
    # Remove old historical data
    # --------------------------------------------------------

    cursor.execute("""
        DELETE FROM api_product_history
    """)

    # Reset auto increment counter if available
    try:

        cursor.execute("""
            DELETE FROM sqlite_sequence
            WHERE name = 'api_product_history'
        """)

    except sqlite3.OperationalError:

        pass

    conn.commit()

    print("Old historical data removed.")

    # --------------------------------------------------------
    # Generate 30 days of historical data
    # --------------------------------------------------------

    print()
    print(f"Creating {NUMBER_OF_DAYS} days of historical data...")
    print()

    random.seed(42)

    today = datetime.now().date()

    total_records = 0

    # --------------------------------------------------------
    # Process each day
    # --------------------------------------------------------

    for day_number in range(NUMBER_OF_DAYS):

        historical_date = today - timedelta(
            days=(NUMBER_OF_DAYS - 1 - day_number)
        )

        api_date = historical_date.strftime(
            "%Y-%m-%d"
        )

        daily_records = 0

        # ----------------------------------------------------
        # Process all 1000 products
        # ----------------------------------------------------

        for product in products:

            (
                product_id,
                title,
                base_price,
                base_rating,
                base_discount,
                base_stock,
                category,
                brand
            ) = product

            # ------------------------------------------------
            # Simulate daily price movement
            # ------------------------------------------------

            price_change = random.uniform(
                -0.08,
                0.08
            )

            historical_price = round(
                base_price * (1 + price_change),
                2
            )

            # Make sure price never becomes negative
            if historical_price < 0.50:

                historical_price = 0.50

            # ------------------------------------------------
            # Simulate discount movement
            # ------------------------------------------------

            discount_change = random.uniform(
                -5,
                5
            )

            historical_discount = round(
                base_discount + discount_change,
                2
            )

            historical_discount = max(
                0,
                min(
                    70,
                    historical_discount
                )
            )

            # ------------------------------------------------
            # Simulate rating movement
            # ------------------------------------------------

            rating_change = random.uniform(
                -0.15,
                0.15
            )

            historical_rating = round(
                base_rating + rating_change,
                2
            )

            historical_rating = max(
                1,
                min(
                    5,
                    historical_rating
                )
            )

            # ------------------------------------------------
            # Simulate stock movement
            # ------------------------------------------------

            stock_change = random.randint(
                -25,
                25
            )

            historical_stock = (
                base_stock + stock_change
            )

            historical_stock = max(
                0,
                historical_stock
            )

            # ------------------------------------------------
            # Insert historical record
            # ------------------------------------------------

            cursor.execute("""
                INSERT INTO api_product_history
                (
                    product_id,
                    title,
                    price,
                    discount,
                    rating,
                    stock,
                    category,
                    brand,
                    api_date
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                product_id,
                title,
                historical_price,
                historical_discount,
                historical_rating,
                historical_stock,
                category,
                brand,
                api_date
            ))

            total_records += 1
            daily_records += 1

        # ----------------------------------------------------
        # Commit after each day
        # ----------------------------------------------------

        conn.commit()

        print(
            f"Day {day_number + 1:02d}/{NUMBER_OF_DAYS} "
            f"| Date: {api_date} "
            f"| Products: {daily_records}"
        )

    # --------------------------------------------------------
    # Final database verification
    # --------------------------------------------------------

    cursor.execute("""
        SELECT COUNT(*)
        FROM api_product_history
    """)

    total_records = cursor.fetchone()[0]

    cursor.execute("""
        SELECT COUNT(DISTINCT product_id)
        FROM api_product_history
    """)

    unique_products = cursor.fetchone()[0]

    cursor.execute("""
        SELECT COUNT(DISTINCT api_date)
        FROM api_product_history
    """)

    unique_days = cursor.fetchone()[0]

    # --------------------------------------------------------
    # Get first and last dates
    # --------------------------------------------------------

    cursor.execute("""
        SELECT
            MIN(api_date),
            MAX(api_date)
        FROM api_product_history
    """)

    first_date, last_date = cursor.fetchone()

    # --------------------------------------------------------
    # Display summary
    # --------------------------------------------------------

    print()
    print("=" * 60)
    print("HISTORICAL API DATA SUMMARY")
    print("=" * 60)

    print(f"Products                : {unique_products}")
    print(f"Days                    : {unique_days}")
    print(f"Total historical records: {total_records}")
    print(f"First date              : {first_date}")
    print(f"Last date               : {last_date}")

    # --------------------------------------------------------
    # Expected record count
    # --------------------------------------------------------

    expected_records = (
        len(products) * NUMBER_OF_DAYS
    )

    print(
        f"Expected records       : {expected_records}"
    )

    # --------------------------------------------------------
    # Display first 10 records
    # --------------------------------------------------------

    print()
    print("=" * 60)
    print("FIRST 10 HISTORICAL RECORDS")
    print("=" * 60)

    cursor.execute("""
        SELECT
            product_id,
            title,
            price,
            discount,
            rating,
            stock,
            api_date
        FROM api_product_history
        ORDER BY history_id
        LIMIT 10
    """)

    rows = cursor.fetchall()

    for row in rows:

        print(
            f"ID: {row[0]} | "
            f"Name: {row[1]} | "
            f"Price: ${row[2]} | "
            f"Discount: {row[3]}% | "
            f"Rating: {row[4]} | "
            f"Stock: {row[5]} | "
            f"Date: {row[6]}"
        )

    # --------------------------------------------------------
    # Close database
    # --------------------------------------------------------

    conn.close()

    print()
    print("=" * 60)
    print("HISTORICAL API DATA COMPLETED")
    print("=" * 60)


# ============================================================
# RUN PROGRAM
# ============================================================

if __name__ == "__main__":

    try:

        create_historical_data()

    except Exception as e:

        print()
        print("=" * 60)
        print("ERROR")
        print("=" * 60)

        print(e)