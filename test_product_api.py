import requests

# ==========================================
# Product API Test
# ==========================================

API_URL = "https://dummyjson.com/products"

print("=" * 50)
print("Market Intelligence Bot - API Test")
print("=" * 50)

try:

    print("\nConnecting to Product API...")

    response = requests.get(
        API_URL,
        timeout=30
    )

    print("Status Code:", response.status_code)

    if response.status_code == 200:

        data = response.json()

        products = data.get("products", [])

        print("\n==========================================")
        print("API CONNECTION SUCCESSFUL")
        print("==========================================")

        print("Total Products Received:", len(products))

        print("\nFirst 10 Products:")
        print("------------------------------------------")

        for product in products[:10]:

            print(
                f"ID: {product.get('id')} | "
                f"Name: {product.get('title')} | "
                f"Price: ${product.get('price')} | "
                f"Rating: {product.get('rating')} | "
                f"Category: {product.get('category')}"
            )

        print("\n==========================================")
        print("API TEST COMPLETED")
        print("==========================================")

    else:

        print("\nAPI request failed.")
        print("Status Code:", response.status_code)
        print("Response:", response.text)

except requests.exceptions.ConnectionError:

    print("\nERROR: Internet connection problem.")

except requests.exceptions.Timeout:

    print("\nERROR: API request timed out.")

except requests.exceptions.RequestException as e:

    print("\nERROR:", e)

except Exception as e:

    print("\nUnexpected Error:", e)