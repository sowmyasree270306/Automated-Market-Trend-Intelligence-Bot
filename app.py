from flask import Flask, render_template, request, redirect, session
import pandas as pd
import sqlite3

app = Flask(__name__)
app.secret_key = "marketbot"


# ==========================================
# Database Connection
# ==========================================

def get_db_connection():
    conn = sqlite3.connect("database.db")
    conn.row_factory = sqlite3.Row
    return conn


# ==========================================
# Load Amazon Dataset
# ==========================================

amazon = pd.read_csv("dataset/amazon.csv")

amazon["discounted_price"] = (
    amazon["discounted_price"]
    .astype(str)
    .str.replace("₹", "", regex=False)
    .str.replace(",", "", regex=False)
)

amazon["actual_price"] = (
    amazon["actual_price"]
    .astype(str)
    .str.replace("₹", "", regex=False)
    .str.replace(",", "", regex=False)
)

amazon["discount_percentage"] = (
    amazon["discount_percentage"]
    .astype(str)
    .str.replace("%", "", regex=False)
)

amazon["discounted_price"] = pd.to_numeric(
    amazon["discounted_price"],
    errors="coerce"
)

amazon["actual_price"] = pd.to_numeric(
    amazon["actual_price"],
    errors="coerce"
)

amazon["discount_percentage"] = pd.to_numeric(
    amazon["discount_percentage"],
    errors="coerce"
)

amazon["rating"] = pd.to_numeric(
    amazon["rating"],
    errors="coerce"
)

amazon["rating_count"] = pd.to_numeric(
    amazon["rating_count"],
    errors="coerce"
)


# ==========================================
# Load Flipkart Dataset
# ==========================================

flipkart = pd.read_csv("dataset/flipkart.csv")


# ==========================================
# Clean Flipkart Selling Price
# ==========================================

flipkart["Selling Price"] = (
    flipkart["Selling Price"]
    .astype(str)
    .str.replace("₹", "", regex=False)
    .str.replace(",", "", regex=False)
    .str.strip()
)


# ==========================================
# Clean Flipkart MRP
# ==========================================

flipkart["MRP"] = (
    flipkart["MRP"]
    .astype(str)
    .str.replace("₹", "", regex=False)
    .str.replace(",", "", regex=False)
    .str.strip()
)


# ==========================================
# Convert Flipkart Numeric Columns
# ==========================================

flipkart["Selling Price"] = pd.to_numeric(
    flipkart["Selling Price"],
    errors="coerce"
)

flipkart["MRP"] = pd.to_numeric(
    flipkart["MRP"],
    errors="coerce"
)

flipkart["Ratings"] = pd.to_numeric(
    flipkart["Ratings"],
    errors="coerce"
)

flipkart["No_of_ratings"] = pd.to_numeric(
    flipkart["No_of_ratings"],
    errors="coerce"
)


# ==========================================
# Calculate Flipkart Discount Percentage
# ==========================================

flipkart["Discount"] = (
    (
        flipkart["MRP"] - flipkart["Selling Price"]
    )
    / flipkart["MRP"]
) * 100

flipkart["Discount"] = (
    flipkart["Discount"]
    .replace([float("inf"), -float("inf")], 0)
    .fillna(0)
    .round(2)
)


# ==========================================
# Home
# ==========================================

@app.route("/")
def home():

    return render_template("home.html")


# ==========================================
# Register
# ==========================================

@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        username = request.form["username"]
        email = request.form["email"]
        password = request.form["password"]

        conn = sqlite3.connect("database.db")
        cursor = conn.cursor()

        cursor.execute(
            "SELECT * FROM users WHERE email=?",
            (email,)
        )

        user = cursor.fetchone()

        if user:

            conn.close()

            return "Email already registered. Please login."

        cursor.execute(
            """
            INSERT INTO users(username,email,password)
            VALUES(?,?,?)
            """,
            (username, email, password)
        )

        conn.commit()
        conn.close()

        return redirect("/login")

    return render_template("register.html")


# ==========================================
# Login
# ==========================================

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form["email"]
        password = request.form["password"]

        conn = sqlite3.connect("database.db")
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT * FROM users
            WHERE email=? AND password=?
            """,
            (email, password)
        )

        user = cursor.fetchone()

        conn.close()

        if user:

            session["username"] = user[1]

            return redirect("/dashboard")

        return "Invalid Email or Password"

    return render_template("login.html")


# ==========================================
# Logout
# ==========================================

@app.route("/logout")
def logout():

    session.clear()

    return redirect("/")


# ==========================================
# Dashboard
# ==========================================

@app.route("/dashboard")
def dashboard():

    if "username" not in session:

        return redirect("/login")

    # ======================================
    # Amazon
    # ======================================

    amazon_products = len(amazon)

    amazon_rating = round(
        amazon["rating"].mean(skipna=True),
        2
    )

    amazon_discount = round(
        amazon["discount_percentage"].mean(skipna=True),
        2
    )

    amazon_price = round(
        amazon["discounted_price"].mean(skipna=True),
        2
    )

    amazon_top = (
        amazon.sort_values(
            by="rating",
            ascending=False
        )
        .head(5)
        [["product_name", "rating", "discounted_price"]]
        .to_dict(orient="records")
    )

    # ======================================
    # Flipkart
    # ======================================

    flipkart_products = len(flipkart)

    flipkart_rating = round(
        flipkart["Ratings"].mean(skipna=True),
        2
    )

    flipkart_discount = round(
        flipkart["Discount"].mean(skipna=True),
        2
    )

    flipkart_price = round(
        flipkart["Selling Price"].mean(skipna=True),
        2
    )

    flipkart_top = (
        flipkart.sort_values(
            by="Ratings",
            ascending=False
        )
        .head(5)
        [["Name", "Ratings", "Selling Price"]]
        .to_dict(orient="records")
    )

    return render_template(
        "dashboard.html",

        username=session["username"],

        amazon_products=amazon_products,
        amazon_rating=amazon_rating,
        amazon_discount=amazon_discount,
        amazon_price=amazon_price,

        flipkart_products=flipkart_products,
        flipkart_rating=flipkart_rating,
        flipkart_discount=flipkart_discount,
        flipkart_price=flipkart_price,

        amazon_top=amazon_top,
        flipkart_top=flipkart_top
    )


# ==========================================
# Search Products
# ==========================================

@app.route("/search", methods=["GET", "POST"])
def search():

    if "username" not in session:

        return redirect("/login")

    amazon_results = []
    flipkart_results = []

    if request.method == "POST":

        keyword = request.form["keyword"]

        amazon_results = amazon[
            amazon["product_name"]
            .str.contains(
                keyword,
                case=False,
                na=False
            )
        ].to_dict(orient="records")

        flipkart_results = flipkart[
            flipkart["Name"]
            .str.contains(
                keyword,
                case=False,
                na=False
            )
        ].to_dict(orient="records")

    return render_template(
        "search.html",
        amazon_results=amazon_results,
        flipkart_results=flipkart_results
    )


# ==========================================
# Compare Products
# ==========================================

@app.route("/compare", methods=["GET", "POST"])
def compare():

    if "username" not in session:
        return redirect("/login")

    # Load only verified product mappings
    mapping = pd.read_csv(
        "dataset/product_mapping.csv"
    ).fillna("")

    amazon_product = None
    flipkart_product = None
    match_found = False
    selected_id = ""

    if request.method == "POST":

        selected_id = request.form.get(
            "amazon_product_id",
            ""
        ).strip()

        # Find selected verified mapping
        selected_mapping = mapping[
            mapping["amazon_product_id"].astype(str)
            == selected_id
        ]

        if not selected_mapping.empty:

            match = selected_mapping.iloc[0]

            # Find exact Amazon product
            amazon_match = amazon[
                amazon["product_id"].astype(str)
                == selected_id
            ]

            # Find exact Flipkart product
            flipkart_match = flipkart[
                flipkart["Name"].astype(str)
                == str(match["flipkart_product_name"])
            ]

            if not amazon_match.empty:

                amazon_product = (
                    amazon_match
                    .iloc[0]
                    .to_dict()
                )

            if not flipkart_match.empty:

                flipkart_product = (
                    flipkart_match
                    .iloc[0]
                    .to_dict()
                )

            # Comparison is valid only when BOTH exist
            if amazon_product and flipkart_product:

                match_found = True

    return render_template(
        "compare.html",

        verified_products=mapping.to_dict(
            "records"
        ),

        amazon=amazon_product,

        flipkart=flipkart_product,

        match_found=match_found,

        selected_id=selected_id
    )


# ==========================================
# Analytics
# ==========================================

@app.route("/analytics")
def analytics():

    if "username" not in session:

        return redirect("/login")

    conn = sqlite3.connect("database.db")

    # ======================================
    # API DAILY TREND DATA
    # ======================================

    daily_data = pd.read_sql_query(
        """
        SELECT
            api_date,
            AVG(price) AS avg_price,
            AVG(discount) AS avg_discount,
            AVG(rating) AS avg_rating,
            AVG(stock) AS avg_stock
        FROM api_product_history
        GROUP BY api_date
        ORDER BY api_date
        """,
        conn
    )

    # ======================================
    # API CATEGORY DATA
    # ======================================

    category_data = pd.read_sql_query(
        """
        SELECT
            category,
            COUNT(*) AS product_count
        FROM api_products
        GROUP BY category
        ORDER BY product_count DESC
        """,
        conn
    )

    # ======================================
    # TOP DISCOUNTED PRODUCTS
    # ======================================

    top_discount_data = pd.read_sql_query(
        """
        SELECT
            title,
            price,
            discount_percentage,
            rating,
            stock
        FROM api_products
        ORDER BY discount_percentage DESC
        LIMIT 10
        """,
        conn
    )

    # ======================================
    # SUMMARY VALUES
    # ======================================

    total_api_products = pd.read_sql_query(
        """
        SELECT COUNT(*) AS total
        FROM api_products
        """,
        conn
    ).iloc[0]["total"]

    avg_price = pd.read_sql_query(
        """
        SELECT AVG(price) AS value
        FROM api_products
        """,
        conn
    ).iloc[0]["value"]

    avg_rating = pd.read_sql_query(
        """
        SELECT AVG(rating) AS value
        FROM api_products
        """,
        conn
    ).iloc[0]["value"]

    avg_discount = pd.read_sql_query(
        """
        SELECT AVG(discount_percentage) AS value
        FROM api_products
        """,
        conn
    ).iloc[0]["value"]

    conn.close()

    return render_template(
        "analytics.html",

        daily_dates=daily_data[
            "api_date"
        ].tolist(),

        daily_prices=daily_data[
            "avg_price"
        ].round(2).tolist(),

        daily_discounts=daily_data[
            "avg_discount"
        ].round(2).tolist(),

        daily_ratings=daily_data[
            "avg_rating"
        ].round(2).tolist(),

        daily_stock=daily_data[
            "avg_stock"
        ].round(2).tolist(),

        categories=category_data[
            "category"
        ].tolist(),

        category_counts=category_data[
            "product_count"
        ].tolist(),

        top_products=top_discount_data.to_dict(
            "records"
        ),

        total_api_products=int(
            total_api_products
        ),

        avg_price=round(
            avg_price,
            2
        ),

        avg_rating=round(
            avg_rating,
            2
        ),

        avg_discount=round(
            avg_discount,
            2
        )
    )


# ==========================================
# Report
# ==========================================

@app.route("/report")
def report():

    if "username" not in session:

        return redirect("/login")

    report = {

        "Amazon Total Products":
        len(amazon),

        "Amazon Average Rating":
        round(
            amazon["rating"].mean(
                skipna=True
            ),
            2
        ),

        "Amazon Average Discount":
        round(
            amazon[
                "discount_percentage"
            ].mean(
                skipna=True
            ),
            2
        ),

        "Amazon Average Price":
        round(
            amazon[
                "discounted_price"
            ].mean(
                skipna=True
            ),
            2
        ),

        "Flipkart Total Products":
        len(flipkart),

        "Flipkart Average Rating":
        round(
            flipkart[
                "Ratings"
            ].mean(
                skipna=True
            ),
            2
        ),

        "Flipkart Average Discount":
        round(
            flipkart[
                "Discount"
            ].mean(
                skipna=True
            ),
            2
        ),

        "Flipkart Average Price":
        round(
            flipkart[
                "Selling Price"
            ].mean(
                skipna=True
            ),
            2
        )
    }

    return render_template(
        "report.html",
        report=report
    )


# ==========================================
# API PRODUCT EXPLORER
# ==========================================

# ==========================================
# API PRODUCT EXPLORER
# ==========================================

@app.route("/api-products")
def api_product_explorer():

    if "username" not in session:
        return redirect("/login")

    # ------------------------------------------
    # Currency conversion
    # API prices are USD.
    # Project displays INR.
    # ------------------------------------------
    USD_TO_INR = 85

    # ------------------------------------------
    # Get filter values
    # ------------------------------------------
    search = request.args.get("search", "").strip()
    category = request.args.get("category", "").strip()
    brand = request.args.get("brand", "").strip()
    min_price = request.args.get("min_price", "").strip()
    max_price = request.args.get("max_price", "").strip()
    min_rating = request.args.get("min_rating", "").strip()
    min_discount = request.args.get("min_discount", "").strip()
    stock_status = request.args.get("stock_status", "").strip()

    # ------------------------------------------
    # Database connection
    # ------------------------------------------
    conn = sqlite3.connect("database.db")
    conn.row_factory = sqlite3.Row

    # ------------------------------------------
    # Base SQL query
    # ------------------------------------------
    query = """
        SELECT
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
        FROM api_products
        WHERE 1=1
    """

    params = []

    # ==========================================
    # SMART PRODUCT SEARCH
    # ==========================================

    if search:

        search_lower = search.lower().strip()

        # --------------------------------------
        # MOBILE / PHONE
        # --------------------------------------

        if search_lower in [
            "mobile",
            "mobiles",
            "phone",
            "phones",
            "smartphone",
            "smartphones"
        ]:

            query += """
                AND (
                    LOWER(category) = 'smartphones'
                    OR LOWER(title) LIKE '%iphone%'
                    OR LOWER(title) LIKE '%phone%'
                    OR LOWER(title) LIKE '%smartphone%'
                    OR LOWER(title) LIKE '%android%'
                )
            """

        # --------------------------------------
        # MOBILE ACCESSORIES
        # --------------------------------------

        elif search_lower in [
            "mobile accessories",
            "phone accessories",
            "accessories"
        ]:

            query += """
                AND LOWER(category) = 'mobile-accessories'
            """

        # --------------------------------------
        # TV
        # --------------------------------------

        elif search_lower in [
            "tv",
            "television",
            "televisions"
        ]:

            query += """
                AND (
                    LOWER(title) LIKE '%tv%'
                    OR LOWER(title) LIKE '%television%'
                )
            """

        # --------------------------------------
        # LAPTOP
        # --------------------------------------

        elif search_lower in [
            "laptop",
            "laptops",
            "notebook",
            "notebooks"
        ]:

            query += """
                AND LOWER(category) = 'laptops'
            """

        # --------------------------------------
        # TABLET
        # --------------------------------------

        elif search_lower in [
            "tablet",
            "tablets",
            "ipad"
        ]:

            query += """
                AND LOWER(category) = 'tablets'
            """

        # --------------------------------------
        # SHOES
        # --------------------------------------

        elif search_lower in [
            "shoe",
            "shoes",
            "footwear"
        ]:

            query += """
                AND (
                    LOWER(category) = 'mens-shoes'
                    OR LOWER(category) = 'womens-shoes'
                )
            """

        # --------------------------------------
        # MEN'S SHOES
        # --------------------------------------

        elif search_lower in [
            "men shoes",
            "mens shoes",
            "men's shoes"
        ]:

            query += """
                AND LOWER(category) = 'mens-shoes'
            """

        # --------------------------------------
        # WOMEN'S SHOES
        # --------------------------------------

        elif search_lower in [
            "women shoes",
            "womens shoes",
            "women's shoes"
        ]:

            query += """
                AND LOWER(category) = 'womens-shoes'
            """

        # --------------------------------------
        # WATCHES
        # --------------------------------------

        elif search_lower in [
            "watch",
            "watches"
        ]:

            query += """
                AND (
                    LOWER(category) = 'mens-watches'
                    OR LOWER(category) = 'womens-watches'
                )
            """

        # --------------------------------------
        # GROCERIES
        # --------------------------------------

        elif search_lower in [
            "grocery",
            "groceries"
        ]:

            query += """
                AND LOWER(category) = 'groceries'
            """

        # --------------------------------------
        # VEGETABLES
        # --------------------------------------

        elif search_lower in [
            "vegetable",
            "vegetables",
            "veggie",
            "veggies"
        ]:

            query += """
                AND LOWER(category) = 'groceries'
                AND (
                    LOWER(title) LIKE '%vegetable%'
                    OR LOWER(title) LIKE '%tomato%'
                    OR LOWER(title) LIKE '%potato%'
                    OR LOWER(title) LIKE '%onion%'
                    OR LOWER(title) LIKE '%carrot%'
                    OR LOWER(title) LIKE '%cucumber%'
                    OR LOWER(title) LIKE '%spinach%'
                    OR LOWER(title) LIKE '%pepper%'
                    OR LOWER(title) LIKE '%broccoli%'
                    OR LOWER(title) LIKE '%cauliflower%'
                    OR LOWER(title) LIKE '%lettuce%'
                    OR LOWER(title) LIKE '%peas%'
                    OR LOWER(title) LIKE '%beans%'
                )
            """

        # --------------------------------------
        # FRUITS
        # --------------------------------------

        elif search_lower in [
            "fruit",
            "fruits"
        ]:

            query += """
                AND LOWER(category) = 'groceries'
                AND (
                    LOWER(title) LIKE '%fruit%'
                    OR LOWER(title) LIKE '%apple%'
                    OR LOWER(title) LIKE '%banana%'
                    OR LOWER(title) LIKE '%orange%'
                    OR LOWER(title) LIKE '%mango%'
                    OR LOWER(title) LIKE '%grape%'
                    OR LOWER(title) LIKE '%watermelon%'
                    OR LOWER(title) LIKE '%pineapple%'
                    OR LOWER(title) LIKE '%strawberry%'
                )
            """

        # --------------------------------------
        # SNACKS
        # --------------------------------------

        elif search_lower in [
            "snack",
            "snacks"
        ]:

            query += """
                AND LOWER(category) = 'groceries'
                AND (
                    LOWER(title) LIKE '%snack%'
                    OR LOWER(title) LIKE '%chips%'
                    OR LOWER(title) LIKE '%biscuit%'
                    OR LOWER(title) LIKE '%cookie%'
                    OR LOWER(title) LIKE '%cracker%'
                    OR LOWER(title) LIKE '%crisps%'
                    OR LOWER(title) LIKE '%candy%'
                    OR LOWER(title) LIKE '%chocolate%'
                    OR LOWER(title) LIKE '%popcorn%'
                )
            """

        # --------------------------------------
        # DRINKS / BEVERAGES
        # --------------------------------------

        elif search_lower in [
            "drink",
            "drinks",
            "beverage",
            "beverages",
            "cool drinks"
        ]:

            query += """
                AND LOWER(category) = 'groceries'
                AND (
                    LOWER(title) LIKE '%drink%'
                    OR LOWER(title) LIKE '%juice%'
                    OR LOWER(title) LIKE '%water%'
                    OR LOWER(title) LIKE '%soda%'
                    OR LOWER(title) LIKE '%cola%'
                    OR LOWER(title) LIKE '%coffee%'
                    OR LOWER(title) LIKE '%tea%'
                )
            """

        # --------------------------------------
        # NORMAL SEARCH
        # --------------------------------------

        else:

            keyword = f"%{search_lower}%"

            query += """
                AND (
                    LOWER(title) LIKE ?
                    OR LOWER(category) LIKE ?
                    OR LOWER(brand) LIKE ?
                )
            """

            params.extend([
                keyword,
                keyword,
                keyword
            ])

    # ==========================================
    # CATEGORY FILTER
    # ==========================================

    if category:

        query += """
            AND LOWER(category) = LOWER(?)
        """

        params.append(category)

    # ==========================================
    # BRAND FILTER
    # ==========================================

    if brand:

        query += """
            AND LOWER(brand) = LOWER(?)
        """

        params.append(brand)

    # ==========================================
    # MINIMUM PRICE - INR
    # ==========================================

    if min_price:

        try:

            minimum = float(min_price)

            query += """
                AND price >= ?
            """

            params.append(
                minimum / USD_TO_INR
            )

        except ValueError:
            pass

    # ==========================================
    # MAXIMUM PRICE - INR
    # ==========================================

    if max_price:

        try:

            maximum = float(max_price)

            query += """
                AND price <= ?
            """

            params.append(
                maximum / USD_TO_INR
            )

        except ValueError:
            pass

    # ==========================================
    # MINIMUM RATING
    # ==========================================

    if min_rating:

        try:

            rating_value = float(min_rating)

            query += """
                AND rating >= ?
            """

            params.append(rating_value)

        except ValueError:
            pass

    # ==========================================
    # MINIMUM DISCOUNT
    # ==========================================

    if min_discount:

        try:

            discount_value = float(min_discount)

            query += """
                AND discount_percentage >= ?
            """

            params.append(discount_value)

        except ValueError:
            pass

    # ==========================================
    # STOCK FILTER
    # ==========================================

    if stock_status == "in_stock":

        query += """
            AND stock > 0
        """

    elif stock_status == "out_of_stock":

        query += """
            AND stock = 0
        """

    # ==========================================
    # SORTING
    # ==========================================

    query += """
        ORDER BY rating DESC, discount_percentage DESC
    """

    # ==========================================
    # GET FILTERED PRODUCTS
    # ==========================================

    all_products = conn.execute(
        query,
        params
    ).fetchall()

    total_matching = len(all_products)

    # ==========================================
    # PAGINATION
    # ==========================================

    try:

        page = int(
            request.args.get(
                "page",
                1
            )
        )

    except ValueError:

        page = 1

    if page < 1:
        page = 1

    per_page = 20

    total_pages = max(
        1,
        (total_matching + per_page - 1)
        // per_page
    )

    if page > total_pages:
        page = total_pages

    start = (
        page - 1
    ) * per_page

    products = all_products[
        start:start + per_page
    ]

    # ==========================================
    # CONVERT SQLITE ROWS TO DICTIONARIES
    # AND USD → INR
    # ==========================================

    product_list = []

    for product in products:

        product_dict = dict(product)

        product_dict["price_inr"] = round(
            float(
                product_dict["price"]
            ) * USD_TO_INR,
            2
        )

        product_list.append(
            product_dict
        )

    # ==========================================
    # CATEGORIES
    # ==========================================

    categories = conn.execute(
        """
        SELECT DISTINCT category
        FROM api_products
        WHERE category IS NOT NULL
        AND category != ''
        ORDER BY category
        """
    ).fetchall()

    categories = [
        row["category"]
        for row in categories
    ]

    # ==========================================
    # BRANDS
    # ==========================================

    brands = conn.execute(
        """
        SELECT DISTINCT brand
        FROM api_products
        WHERE brand IS NOT NULL
        AND brand != ''
        ORDER BY brand
        """
    ).fetchall()

    brands = [
        row["brand"]
        for row in brands
    ]

    # ==========================================
    # OVERALL API STATISTICS
    # ==========================================

    stats = conn.execute(
        """
        SELECT
            COUNT(*) AS total_products,
            AVG(price) AS avg_price,
            AVG(rating) AS avg_rating,
            AVG(discount_percentage) AS avg_discount
        FROM api_products
        """
    ).fetchone()

    conn.close()

    # ==========================================
    # STATISTICS CONVERSION
    # ==========================================

    avg_price_inr = round(
        float(
            stats["avg_price"] or 0
        ) * USD_TO_INR,
        2
    )

    avg_rating_value = round(
        float(
            stats["avg_rating"] or 0
        ),
        2
    )

    avg_discount_value = round(
        float(
            stats["avg_discount"] or 0
        ),
        2
    )

    # ==========================================
    # RENDER PAGE
    # ==========================================

    return render_template(
        "api_products.html",

        products=product_list,

        categories=categories,

        brands=brands,

        search=search,

        selected_category=category,

        selected_brand=brand,

        min_price=min_price,

        max_price=max_price,

        min_rating=min_rating,

        min_discount=min_discount,

        stock_status=stock_status,

        total_matching=total_matching,

        page=page,

        total_pages=total_pages,

        per_page=per_page,

        total_api_products=int(
            stats["total_products"] or 0
        ),

        avg_price=avg_price_inr,

        avg_rating=avg_rating_value,

        avg_discount=avg_discount_value,

        usd_to_inr=USD_TO_INR
    )
# ==========================================
# Error Page
# ==========================================

@app.errorhandler(404)
def page_not_found(error):
    return "<h2>404 - Page Not Found</h2>", 404


# ==========================================
# Run Flask App
# ==========================================

if __name__ == "__main__":
    app.run(
        debug=True,
        host="127.0.0.1",
        port=5000
    )