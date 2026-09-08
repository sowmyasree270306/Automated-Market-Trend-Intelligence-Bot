import requests

API_URL = "https://dummyjson.com/products?limit=0"

print("=" * 60)
print("MARKET INTELLIGENCE BOT - ECOMMERCE API TEST")
print("=" * 60)

response = requests.get(API_URL, timeout=30)

print("\nStatus Code:", response.status_code)

if response.status_code == 200:

    data = response.json()

    print("\nAPI CONNECTION SUCCESSFUL")

    print("\nTotal Products:", len(data["products"]))

    print("\nFirst 10 Products:")
    print("-" * 60)

    for product in data["products"][:10]:

        print(
            f"ID: {product['id']} | "
            f"Name: {product['title']} | "
            f"Price: ${product['price']} | "
            f"Discount: {product['discountPercentage']}% | "
            f"Rating: {product['rating']} | "
            f"Stock: {product['stock']} | "
            f"Category: {product['category']}"
        )

else:

    print("\nAPI CONNECTION FAILED")
    print(response.text)