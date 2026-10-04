"""Normalize the four marketplace source CSVs into one app-ready catalog.

Place this file in the project's dataset/ folder (recommended) or project root.
Run: python update_dataset.py
"""
from pathlib import Path
import re
import pandas as pd

SCRIPT_DIR = Path(__file__).resolve().parent
DATASET_DIR = SCRIPT_DIR if SCRIPT_DIR.name.lower() == "dataset" else SCRIPT_DIR / "dataset"
USD_TO_INR = 95.50  # Change only if your project uses a different conversion rate.

FLIPKART_FILES = {
    "flipkart_mobile_data.csv": "Mobiles",
    "flipkart_laptops.csv": "Laptops",
    "flipkart_earphones.csv": "Earphones",
}
SOURCES = [
    ("amazon.csv", "Amazon", "INR"),
    ("croma_products_final.csv", "Croma", "INR"),
    ("BestBuy_Products.csv", "Best Buy", "USD"),
]


def clean(value):
    if value is None or pd.isna(value):
        return ""
    return re.sub(r"\s+", " ", str(value)).strip()


def col(df, *names):
    lookup = {re.sub(r"[^a-z0-9]", "", str(c).lower()): c for c in df.columns}
    for name in names:
        found = lookup.get(re.sub(r"[^a-z0-9]", "", name.lower()))
        if found is not None:
            return found
    return None


def val(row, column):
    return row.get(column) if column is not None else None


def number(value):
    text = clean(value).replace(",", "")
    if not text or text.lower() in {"nan", "none", "null", "n/a", "na", "-"}:
        return None
    match = re.search(r"-?\d+(?:\.\d+)?", text)
    if not match:
        return None
    try:
        result = float(match.group())
        return result if result > 0 else None
    except ValueError:
        return None


def count(value):
    text = clean(value).replace(",", "")
    if not text:
        return None
    # Flipkart's combined field is e.g. "58,788 Ratings & 3,425 Reviews".
    reviews = re.search(r"([\d]+)\s*reviews?", text, re.I)
    if reviews:
        return int(reviews.group(1))
    match = re.search(r"\d+", text)
    return int(match.group()) if match else None


def first_image(value):
    text = clean(value)
    if not text:
        return ""
    # Croma stores multiple URLs separated by semicolons.
    match = re.search(r"https?://[^\s;|,]+", text)
    return match.group(0).rstrip("'\"])") if match else ""


def clean_url(value):
    url = clean(value)
    if not url:
        return ""
    # Repair malformed Flipkart URLs that contain the host twice.
    url = re.sub(r"^(https?://www\.flipkart\.com)https?://www\.flipkart\.com", r"\1", url, flags=re.I)
    return url if url.startswith(("http://", "https://")) else ""


def category_text(value, fallback="Electronics"):
    text = clean(value)
    if not text:
        return fallback
    # Amazon categories are pipe-delimited; use the most specific final segment.
    if "|" in text:
        text = text.split("|")[-1]
    return text.replace("&", " & ").strip() or fallback


def make_record(row, market, category_hint=None):
    if market == "Flipkart":
        name_c = col(row.to_frame().T, "Title", "Product Name", "Name")
        price_c = col(row.to_frame().T, "Price", "Selling Price")
        mrp_c = col(row.to_frame().T, "Original Price", "MRP", "List Price")
        rating_c = col(row.to_frame().T, "Rating")
        reviews_c = col(row.to_frame().T, "Ratings & Reviews", "Rating Count", "Reviews")
        discount_c = col(row.to_frame().T, "Discount")
        image_c = col(row.to_frame().T, "Image URL", "Image", "Images")
        url_c = col(row.to_frame().T, "Product Link", "Product URL", "URL")
        category_c = col(row.to_frame().T, "Category")
        brand_c = col(row.to_frame().T, "Brand")
        features_c = col(row.to_frame().T, "Key Features", "Features", "Description")
        id_c = col(row.to_frame().T, "Product ID", "ID", "SKU")
        availability_c = col(row.to_frame().T, "Availability", "Stock")
    elif market == "Amazon":
        df = row.to_frame().T
        name_c = col(df, "product_name", "title", "name")
        price_c = col(df, "discounted_price", "selling_price", "price")
        mrp_c = col(df, "actual_price", "original_price", "mrp")
        rating_c = col(df, "rating")
        reviews_c = col(df, "rating_count", "reviews", "review_count")
        discount_c = col(df, "discount_percentage", "discount")
        image_c = col(df, "img_link", "image", "image_url")
        url_c = col(df, "product_link", "product_url", "url")
        category_c = col(df, "category")
        brand_c = col(df, "brand")
        features_c = col(df, "about_product", "key_features", "features")
        id_c = col(df, "product_id", "asin", "sku", "id")
        availability_c = col(df, "availability", "stock")
    else:
        df = row.to_frame().T
        name_c = col(df, "name", "product_name", "product name", "title", "product")
        price_c = col(df, "price", "discounted_price", "selling_price", "sale_price")
        mrp_c = col(df, "mrp", "original_price", "original_price", "actual_price", "list_price")
        rating_c = col(df, "rating")
        reviews_c = col(df, "reviews", "review_count", "rating_count", "ratings & reviews")
        discount_c = col(df, "discount", "discount_percentage")
        image_c = col(df, "images", "image", "image_url", "image url", "img_link")
        url_c = col(df, "link", "product_url", "product link", "url")
        category_c = col(df, "category")
        brand_c = col(df, "brand")
        features_c = col(df, "features", "key_features", "about_product", "overview")
        id_c = col(df, "product_id", "sku", "asin", "id")
        availability_c = col(df, "availability", "stock")

    name = clean(val(row, name_c))
    price = number(val(row, price_c))
    if not name or price is None:
        return None
    mrp = number(val(row, mrp_c))
    currency = "USD" if market == "Best Buy" else "INR"
    if market == "Best Buy":
        price_inr = round(price * USD_TO_INR, 2)
        mrp_inr = round(mrp * USD_TO_INR, 2) if mrp else None
    else:
        price_inr, mrp_inr = price, mrp
    discount = number(val(row, discount_c))
    if mrp_inr and mrp_inr >= price_inr:
        discount = round((mrp_inr - price_inr) / mrp_inr * 100, 2)
    brand = clean(val(row, brand_c))
    if not brand:
        brand = name.split()[0] if name else "Unknown"
    return {
        "marketplace": market,
        "product_id": clean(val(row, id_c)),
        "product_name": name,
        "brand": brand,
        "category": category_text(val(row, category_c), category_hint or "Electronics"),
        "price": price,
        "mrp": mrp,
        "original_price": price,
        "original_mrp": mrp,
        "currency": currency,
        "price_inr": price_inr,
        "mrp_inr": mrp_inr,
        "discount": discount,
        "rating": number(val(row, rating_c)),
        "reviews": count(val(row, reviews_c)),
        "image": first_image(val(row, image_c)),
        "product_url": clean_url(val(row, url_c)),
        "availability": clean(val(row, availability_c)) or "Unknown",
        "key_features": clean(val(row, features_c)),
    }


def read_source(path):
    for enc in ("utf-8-sig", "utf-8", "latin1"):
        try:
            return pd.read_csv(path, encoding=enc, low_memory=False)
        except UnicodeDecodeError:
            continue
    return pd.read_csv(path, low_memory=False)


def main():
    if not DATASET_DIR.exists():
        raise FileNotFoundError(f"Dataset folder not found: {DATASET_DIR}")
    records = []
    for filename, category in FLIPKART_FILES.items():
        path = DATASET_DIR / filename
        if not path.exists():
            print(f"Missing source: {path}")
            continue
        df = read_source(path)
        for _, row in df.iterrows():
            record = make_record(row, "Flipkart", category)
            if record:
                records.append(record)
        print(f"Flipkart / {category}: {len(df):,} source rows")
    for filename, market, _currency in SOURCES:
        path = DATASET_DIR / filename
        if not path.exists():
            print(f"Missing source: {path}")
            continue
        df = read_source(path)
        for _, row in df.iterrows():
            record = make_record(row, market)
            if record:
                records.append(record)
        print(f"{market}: {len(df):,} source rows")

    if not records:
        raise RuntimeError(f"No valid products found in {DATASET_DIR}")
    data = pd.DataFrame(records)
    # Deduplicate only exact same-marketplace listing URLs/IDs. Keep distinct variants.
    data["_url_key"] = data["product_url"].str.lower().str.strip()
    data["_id_key"] = data["product_id"].str.lower().str.strip()
    data["_name_key"] = data["product_name"].str.lower().str.replace(r"\s+", " ", regex=True).str.strip()
    data["_dedupe_key"] = data["_url_key"].where(data["_url_key"].ne(""), data["_id_key"])
    data["_dedupe_key"] = data["_dedupe_key"].where(data["_dedupe_key"].ne(""), data["_name_key"])
    before = len(data)
    data = data.drop_duplicates(subset=["marketplace", "_dedupe_key"], keep="first").drop(columns=["_url_key", "_id_key", "_name_key", "_dedupe_key"])
    output = DATASET_DIR / "all_marketplaces.csv"
    data.to_csv(output, index=False, encoding="utf-8-sig")
    # Keep the historical merged filename synchronized, not as a second input.
    data.to_csv(DATASET_DIR / "merged_electronics_data.csv", index=False, encoding="utf-8-sig")
    data[data.marketplace.eq("Flipkart")].to_csv(DATASET_DIR / "flipkart_products_new.csv", index=False, encoding="utf-8-sig")
    data[data.marketplace.eq("Croma")].to_csv(DATASET_DIR / "croma_products_clean.csv", index=False, encoding="utf-8-sig")
    print(f"\nSaved: {output}\nDuplicates removed: {before-len(data):,}\nTotal: {len(data):,}")
    print(data.groupby("marketplace").size().to_string())
    print(f"Best Buy USD conversion used: 1 USD = ₹{USD_TO_INR:.2f}")

if __name__ == "__main__":
    main()
