import pandas as pd
import re
from rapidfuzz import fuzz

# ==========================================
# Load Amazon and Flipkart datasets
# ==========================================

amazon = pd.read_csv("dataset/amazon.csv")
flipkart = pd.read_csv("dataset/flipkart.csv")

print("Amazon products :", len(amazon))
print("Flipkart products:", len(flipkart))


# ==========================================
# Clean product names
# ==========================================

def clean_text(text):

    text = str(text).lower()

    # Remove special characters
    text = re.sub(r"[^a-z0-9\s]", " ", text)

    # Remove extra spaces
    text = re.sub(r"\s+", " ", text).strip()

    return text


amazon["clean_name"] = amazon["product_name"].apply(clean_text)
flipkart["clean_name"] = flipkart["Name"].apply(clean_text)


# ==========================================
# Extract model/number tokens
# ==========================================

def get_numbers(text):

    return set(
        re.findall(
            r"\b[a-z]*\d+[a-z0-9]*\b",
            text.lower()
        )
    )


# ==========================================
# Find possible matching products
# ==========================================

candidates = []

for _, amazon_row in amazon.iterrows():

    amazon_name = amazon_row["clean_name"]

    best_matches = []

    for _, flipkart_row in flipkart.iterrows():

        flipkart_name = flipkart_row["clean_name"]

        # ----------------------------------
        # Name similarity
        # ----------------------------------

        name_score = fuzz.token_set_ratio(
            amazon_name,
            flipkart_name
        )

        # ----------------------------------
        # Model/number similarity
        # ----------------------------------

        amazon_numbers = get_numbers(amazon_name)
        flipkart_numbers = get_numbers(flipkart_name)

        number_score = 0

        if amazon_numbers and flipkart_numbers:

            common_numbers = amazon_numbers.intersection(
                flipkart_numbers
            )

            if common_numbers:
                number_score = 30

        # ----------------------------------
        # Final score
        # ----------------------------------

        final_score = name_score + number_score

        best_matches.append(
            (
                final_score,
                name_score,
                number_score,
                amazon_row["product_id"],
                amazon_row["product_name"],
                flipkart_row["Name"],
                flipkart_row["Brand"],
                flipkart_row["Category"]
            )
        )

    # --------------------------------------
    # Keep best 3 candidates
    # --------------------------------------

    best_matches = sorted(
        best_matches,
        reverse=True
    )[:3]

    for match in best_matches:

        (
            final_score,
            name_score,
            number_score,
            amazon_id,
            amazon_product,
            flipkart_product,
            flipkart_brand,
            flipkart_category
        ) = match

        # Only save reasonably similar products
        if name_score >= 55:

            candidates.append({

                "amazon_product_id":
                    amazon_id,

                "amazon_product_name":
                    amazon_product,

                "flipkart_product_name":
                    flipkart_product,

                "flipkart_brand":
                    flipkart_brand,

                "flipkart_category":
                    flipkart_category,

                "similarity_score":
                    round(name_score, 2),

                "model_match_score":
                    number_score,

                "final_score":
                    round(final_score, 2)
            })


# ==========================================
# Create result DataFrame
# ==========================================

result = pd.DataFrame(candidates)


# ==========================================
# Sort by similarity
# ==========================================

if not result.empty:

    result = result.sort_values(
        by="final_score",
        ascending=False
    )


# ==========================================
# Save candidates
# ==========================================

result.to_csv(
    "dataset/mapping_candidates.csv",
    index=False
)


# ==========================================
# Display results
# ==========================================

print()
print("==========================================")
print("Candidate matching completed")
print("==========================================")

print(
    "Possible candidates:",
    len(result)
)

print()
print("Saved to:")
print("dataset/mapping_candidates.csv")

print()

if not result.empty:

    print("Top 20 candidates:")
    print()

    print(
        result.head(20).to_string(index=False)
    )

else:

    print("No possible matches found.")