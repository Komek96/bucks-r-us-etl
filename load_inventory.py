
import sys
import json
import hashlib
import pandas as pd
from database import get_connection
from extract_inventory import (
    validate_inventory,
    SHEET_URL,
    PRODUCTS_URL,
    STORES_URL
)

inventory = pd.read_csv(SHEET_URL)
inventory_csv = inventory.to_csv(index=False)
delivery_hash = hashlib.sha256(
    inventory_csv.encode("utf-8")
).hexdigest()
print(f"Inventory delivery SHA-256: {delivery_hash}")
with open("delivery_history.json", "r") as file:
    delivery_history = json.load(file)
processed_deliveries = delivery_history["processed_deliveries"]
print(f"Previously processed deliveries: {len(processed_deliveries)}")
if delivery_hash in processed_deliveries:
    print("DUPLICATE DELIVERY DETECTED")
    sys.exit(0)
else:
    print("NEW DELIVERY DETECTED")
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
processed_deliveries.append(delivery_hash)
print("Delivery fingerprint prepared for registration.")
delivery_history["processed_deliveries"] = processed_deliveries
with open("delivery_history.json", "w") as file:
    json.dump(delivery_history, file, indent=2)
print("Delivery fingerprint successfully registered.")
