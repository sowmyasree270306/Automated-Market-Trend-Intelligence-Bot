from pathlib import Path
import re
import py_compile
import pandas as pd


# ============================================================
# FINAL MARKETPLACE MIGRATION
# Amazon + Flipkart + Walmart + Best Buy
# Target -> removed
# ============================================================

BASE_DIR = Path(__file__).resolve().parent
APP_FILE = BASE_DIR / "app.py"
TEMPLATES_DIR = BASE_DIR / "templates"
DATASET_FILE = BASE_DIR / "dataset" / "all_marketplaces.csv"


print()
print("=" * 70)
print("FINAL MARKETPLACE MIGRATION")
print("=" * 70)


# ============================================================
# CHECK FILES
# ============================================================

if not APP_FILE.exists():
    print("ERROR: app.py not found.")
    raise SystemExit(1)

if not TEMPLATES_DIR.exists():
    print("ERROR: templates folder not found.")
    raise SystemExit(1)

if not DATASET_FILE.exists():
    print("ERROR: dataset/all_marketplaces.csv not found.")
    raise SystemExit(1)


# ============================================================
# CHECK DATASET
# ============================================================

print()
print("Checking final dataset...")

df = pd.read_csv(
    DATASET_FILE,
    low_memory=False
)

if "marketplace" not in df.columns:
    print("ERROR: marketplace column is missing.")
    raise SystemExit(1)

df["marketplace"] = (
    df["marketplace"]
    .astype(str)
    .str.strip()
    .str.lower()
)

counts = df["marketplace"].value_counts()


print()
print("Marketplace counts:")
print(
    counts.to_string()
)


required = {
    "amazon",
    "flipkart",
    "walmart",
    "bestbuy"
}

actual = set(
    df["marketplace"].dropna().unique()
)

missing = required - actual

if missing:
    print()
    print("ERROR: Missing marketplaces:")
    print(missing)
    raise SystemExit(1)


print()
print("Dataset validation passed.")


# ============================================================
# READ APP.PY
# ============================================================

print()
print("Updating app.py...")

app = APP_FILE.read_text(
    encoding="utf-8"
)


# ============================================================
# TARGET -> BEST BUY
# ============================================================

replacements = [

    # Marketplace values
    ('"target"', '"bestbuy"'),
    ("'target'", "'bestbuy'"),

    # Display names
    ('"Target"', '"Best Buy"'),
    ("'Target'", "'Best Buy'"),

    # Variables
    ("target_products", "bestbuy_products"),
    ("target_top", "bestbuy_top"),
    ("target_data", "bestbuy_data"),

    # Dataset references
    ("target-products.csv", "BestBuy_Products.csv"),
    ("target_products.csv", "BestBuy_Products.csv"),
    ("target.csv", "BestBuy_Products.csv"),

    # URLs / search links
    ("marketplace=target", "marketplace=bestbuy"),

    # Text
    (
        "Amazon, Flipkart, Walmart and Target",
        "Amazon, Flipkart, Walmart and Best Buy"
    ),

    (
        "Amazon + Flipkart + Walmart + Target",
        "Amazon + Flipkart + Walmart + Best Buy"
    ),

    (
        "Amazon, Flipkart, Walmart & Target",
        "Amazon, Flipkart, Walmart & Best Buy"
    ),

    (
        "Search on Target",
        "Search on Best Buy"
    ),
]


for old, new in replacements:
    app = app.replace(old, new)


# ============================================================
# FIX BEST BUY MARKETPLACE SEARCH
# ============================================================

search_alias = """        # Best Buy UI name -> dataset key
        if market in {
            "best buy",
            "best_buy",
            "best-buy"
        }:
            market = "bestbuy"

"""


search_marker = """        market = normalize_name(
            marketplace
        )
"""

if (
    search_alias not in app
    and search_marker in app
):

    app = app.replace(
        search_marker,
        search_marker + "\n" + search_alias,
        1
    )

    print("Added Best Buy marketplace alias.")


# ============================================================
# ADD IMAGE PLACEHOLDER ROUTE
# ============================================================

if "def product_placeholder(" not in app:

    print("Adding product image placeholder route...")

    placeholder = r'''
# ============================================================
# PRODUCT IMAGE PLACEHOLDER
# ============================================================

@app.route("/product-placeholder")
def product_placeholder():

    return """
    <svg xmlns="http://www.w3.org/2000/svg"
         width="500"
         height="500"
         viewBox="0 0 500 500">

        <defs>
            <linearGradient
                id="bg"
                x1="0%"
                y1="0%"
                x2="100%"
                y2="100%"
            >
                <stop
                    offset="0%"
                    stop-color="#eef2ff"
                />

                <stop
                    offset="100%"
                    stop-color="#e0e7ff"
                />
            </linearGradient>
        </defs>

        <rect
            width="500"
            height="500"
            rx="30"
            fill="url(#bg)"
        />

        <rect
            x="120"
            y="105"
            width="260"
            height="210"
            rx="25"
            fill="white"
            stroke="#c7d2fe"
            stroke-width="8"
        />

        <circle
            cx="190"
            cy="175"
            r="28"
            fill="#6366f1"
        />

        <path
            d="M145 280 L220 215 L270 255 L315 210 L365 280 Z"
            fill="#818cf8"
        />

        <text
            x="250"
            y="370"
            text-anchor="middle"
            font-family="Arial"
            font-size="30"
            font-weight="bold"
            fill="#334155"
        >
            Product Image
        </text>

        <text
            x="250"
            y="410"
            text-anchor="middle"
            font-family="Arial"
            font-size="22"
            fill="#64748b"
        >
            Not available
        </text>

    </svg>
    """

'''

    main_marker = (
        '# ============================================================\n'
        '# MAIN'
    )

    if main_marker in app:

        app = app.replace(
            main_marker,
            placeholder + "\n" + main_marker,
            1
        )

    else:

        main_marker = 'if __name__ == "__main__":'

        if main_marker in app:

            app = app.replace(
                main_marker,
                placeholder + "\n" + main_marker,
                1
            )


# ============================================================
# SAVE APP.PY
# ============================================================

APP_FILE.write_text(
    app,
    encoding="utf-8"
)

print("app.py updated.")


# ============================================================
# UPDATE ALL HTML FILES
# ============================================================

print()
print("Updating HTML templates...")


html_files = list(
    TEMPLATES_DIR.rglob("*.html")
)


for html_file in html_files:

    html = html_file.read_text(
        encoding="utf-8"
    )

    original = html


    # --------------------------------------------------------
    # Target -> Best Buy
    # --------------------------------------------------------

    html = html.replace(
        "Target",
        "Best Buy"
    )


    # --------------------------------------------------------
    # Marketplace key
    # --------------------------------------------------------

    html = re.sub(
        r"marketplace=target\b",
        "marketplace=bestbuy",
        html,
        flags=re.IGNORECASE
    )


    html = re.sub(
        r"marketplace\s*=\s*[\"']target[\"']",
        'marketplace="bestbuy"',
        html,
        flags=re.IGNORECASE
    )


    # --------------------------------------------------------
    # Variables
    # --------------------------------------------------------

    html = html.replace(
        "target_products",
        "bestbuy_products"
    )

    html = html.replace(
        "target_top",
        "bestbuy_top"
    )

    html = html.replace(
        "target_data",
        "bestbuy_data"
    )


    # --------------------------------------------------------
    # Python/Jinja dictionary keys
    # --------------------------------------------------------

    html = re.sub(
        r"\[['\"]target['\"]\]",
        "['bestbuy']",
        html,
        flags=re.IGNORECASE
    )


    html = re.sub(
        r"\[['\"]Target['\"]\]",
        "['bestbuy']",
        html
    )


    # --------------------------------------------------------
    # Target comparison
    # --------------------------------------------------------

    html = re.sub(
        r"==\s*[\"']target[\"']",
        '== "bestbuy"',
        html,
        flags=re.IGNORECASE
    )


    html = re.sub(
        r"==\s*[\"']Target[\"']",
        '== "bestbuy"',
        html
    )


    # --------------------------------------------------------
    # Save only if changed
    # --------------------------------------------------------

    if html != original:

        html_file.write_text(
            html,
            encoding="utf-8"
        )

        print(
            "Updated:",
            html_file.relative_to(BASE_DIR)
        )


# ============================================================
# CHECK APP.PY SYNTAX
# ============================================================

print()
print("Checking app.py syntax...")

try:

    py_compile.compile(
        str(APP_FILE),
        doraise=True
    )

except py_compile.PyCompileError as error:

    print()
    print("ERROR: app.py syntax problem.")
    print(error)
    raise SystemExit(1)

else:

    print("app.py syntax is valid.")


# ============================================================
# CHECK FOR TARGET
# ============================================================

print()
print("Checking remaining Target references...")


files_to_check = [
    APP_FILE
] + html_files


remaining = []


for file_path in files_to_check:

    content = file_path.read_text(
        encoding="utf-8"
    )

    for number, line in enumerate(
        content.splitlines(),
        start=1
    ):

        lower = line.lower()

        if (
            '"target"' in lower
            or "'target'" in lower
            or "target_products" in lower
            or "target_top" in lower
            or "target_data" in lower
            or "marketplace=target" in lower
        ):

            remaining.append(
                (
                    file_path.relative_to(BASE_DIR),
                    number,
                    line.strip()
                )
            )


if remaining:

    print()
    print("Some Target references still exist:")

    for file_path, number, line in remaining[:30]:

        print(
            f"{file_path}:{number}: {line}"
        )

else:

    print(
        "No Target marketplace references found."
    )


# ============================================================
# FINAL RESULT
# ============================================================

print()
print("=" * 70)
print("FINAL MARKETPLACES")
print("=" * 70)

print(
    f"Amazon     : {counts.get('amazon', 0):,}"
)

print(
    f"Flipkart   : {counts.get('flipkart', 0):,}"
)

print(
    f"Walmart    : {counts.get('walmart', 0):,}"
)

print(
    f"Best Buy   : {counts.get('bestbuy', 0):,}"
)

print()
print("=" * 70)
print("MIGRATION COMPLETE")
print("=" * 70)
print()