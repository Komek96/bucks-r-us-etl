import pandas as pd
from database import get_connection

STORES_URL = (
    "https://docs.google.com/spreadsheets/d/"
    "1LfF4pfY7aPECnZJHiw0YsY_AF7WRoNnB1PuFGnJ6npg/"
    "export?format=csv&gid=1763900964"
)

stores = pd.read_csv(STORES_URL)
stores["closed_at"] = pd.to_datetime(
    stores["closed_at"],
    errors="coerce"
)
print("STORES READY FOR LOADING:")
print(stores.to_string(index=False))
print(f"\nTotal stores: {len(stores)}")
print("\nCLOSURE DATE CHECK:")
print(stores[["store_id", "closed_at"]].to_string(index=False))
print("\nColumn type:", stores["closed_at"].dtype)

with get_connection() as conn:
    with conn.cursor() as cursor:
        for _, store in stores.iterrows():

            closed_at = (
                None
                if pd.isna(store["closed_at"])
                else store["closed_at"].to_pydatetime()
            )

            cursor.execute(
                """
                INSERT INTO stores (
                    store_id, address, city, state,
                    zip_code, status, closed_at
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (store_id) DO NOTHING;
                """,
                (
                    store["store_id"],
                    store["address"],
                    store["city"],
                    store["state"],
                    str(store["zip_code"]),
                    store["status"],
                    closed_at
                )
            )

            print(f"Processed store: {store['store_id']}")