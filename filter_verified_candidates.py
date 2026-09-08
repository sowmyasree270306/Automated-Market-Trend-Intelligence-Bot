import pandas as pd
import re

# ==========================================
# Load candidate matches
# ==========================================

candidates = pd.read_csv(
    "dataset/mapping_candidates.csv"
)

print("Total candidates:", len(candidates))


# ==========================================
# Extract numbers from product names
# ==========================================

def extract_numbers(text):

    text = str(text).lower()

    return set(
        re.findall(
            r"\b\d+(?:\.\d+)?\s*(?:gb|mb|kg|inch|inches|cm|mm|w|mah|hz|tb)?\b",
            text
        )
    )


# ==========================================
# Validate important specifications
# ==========================================

verified = []

for _, row in candidates.iterrows():

    amazon_name = str(
        row["amazon_product_name"]
    ).lower()

    flipkart_name = str(
        row["flipkart_product_name"]
    ).lower()

    similarity = float(
        row["similarity_score"]
    )

    # --------------------------------------
    # Only high similarity
    # --------------------------------------

    if similarity < 95:
        continue

    # --------------------------------------
    # Check specifications
    # --------------------------------------

    amazon_specs = extract_numbers(
        amazon_name
    )

    flipkart_specs = extract_numbers(
        flipkart_name
    )

    # If both products contain specifications,
    # require at least one common specification
    if amazon_specs and flipkart_specs:

        common_specs = (
            amazon_specs.intersection(
                flipkart_specs
            )
        )

        if not common_specs:
            continue

    verified.append({

        "amazon_product_id":
            row["amazon_product_id"],

        "amazon_product_name":
            row["amazon_product_name"],

        "flipkart_product_name":
            row["flipkart_product_name"],

        "flipkart_brand":
            row["flipkart_brand"],

        "flipkart_category":
            row["flipkart_category"],

        "similarity_score":
            row["similarity_score"]

    })


# ==========================================
# Remove duplicate Amazon products
# ==========================================

result = pd.DataFrame(verified)

if not result.empty:

    result = result.drop_duplicates(
        subset=[
            "amazon_product_id",
            "flipkart_product_name"
        ]
    )

    result = result.sort_values(
        by="similarity_score",
        ascending=False
    )


# ==========================================
# Save possible verified matches
# ==========================================

result.to_csv(
    "dataset/high_confidence_matches.csv",
    index=False
)


# ==========================================
# Display results
# ==========================================

print()
print("==========================================")
print("High Confidence Matching")
print("==========================================")

print(
    "High-confidence matches:",
    len(result)
)

print()
print("Saved to:")

print(
    "dataset/high_confidence_matches.csv"
)

print()

if not result.empty:

    print("Top matches:")
    print()

    print(
        result.head(30).to_string(
            index=False
        )
    )

else:

    print("No high-confidence matches found.")