import pandas as pd
from database import get_connection

PRODUCTS_URL = (
    "https://docs.google.com/spreadsheets/d/"
    "1LfF4pfY7aPECnZJHiw0YsY_AF7WRoNnB1PuFGnJ6npg/"
    "export?format=csv&gid=2125665780"
)

products = pd.read_csv(PRODUCTS_URL)

print("PRODUCTS READY FOR LOADING:")
print(products.to_string(index=False))
print(f"\nTotal products: {len(products)}")

with get_connection() as conn:
    with conn.cursor() as cursor:
        for _, product in products.iterrows():
            cursor.execute(
                """
                INSERT INTO products (sku, product_name, category, status)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (sku) DO NOTHING;
                """,
                (
                    product["sku"],
                    product["product_name"],
                    product["category"],
                    product["status"]
                )
            )

            print(f"Processed product: {product['sku']}")