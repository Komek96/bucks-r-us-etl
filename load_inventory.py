import pandas as pd
from database import get_connection
from extract_inventory import (
    validate_inventory,
    SHEET_URL,
    PRODUCTS_URL,
    STORES_URL
)

inventory = pd.read_csv(SHEET_URL)
products = pd.read_csv(PRODUCTS_URL)
stores = pd.read_csv(STORES_URL)

print(f"Downloaded {len(inventory)} inventory records.")
print(f"Downloaded {len(products)} products.")
print(f"Downloaded {len(stores)} stores.")

#Inventory Validation

valid_inventory, rejected_inventory = validate_inventory(
    inventory,
    products,
    stores
)

print(f"Valid inventory records: {len(valid_inventory)}")
print(f"Rejected inventory records: {len(rejected_inventory)}")

valid_inventory = valid_inventory.copy()

valid_inventory["inventory_timestamp"] = pd.to_datetime(
    valid_inventory["inventory_timestamp"]
)

print("\nValidated inventory ready for PostgreSQL:")
print(valid_inventory.to_string(index=False))

inserted_count = 0
skipped_count = 0

with get_connection() as conn:
    with conn.cursor() as cursor:
        for _, item in valid_inventory.iterrows():
            cursor.execute(
                """
                INSERT INTO inventory (
                    store_id,
                    sku,
                    quantity_on_hand,
                    inventory_timestamp
                )
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (store_id, sku, inventory_timestamp)
                DO NOTHING;
                """,
                (
                    item["store_id"],
                    item["sku"],
                    int(item["quantity_on_hand"]),
                    item["inventory_timestamp"].to_pydatetime()
                )
            )

            if cursor.rowcount == 1:
                inserted_count += 1
                print(f"Inserted inventory: {item['store_id']} - {item['sku']}")
            else:
                skipped_count += 1
                print(f"Skipped existing inventory: {item['store_id']} - {item['sku']}")
                

print(f"\nTotal new inventory records inserted: {inserted_count}")
print(f"Total existing inventory records skipped: {skipped_count}")