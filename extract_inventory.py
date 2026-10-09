import pandas as pd
import hashlib
import json
import sys


SHEET_URL = "https://docs.google.com/spreadsheets/d/1LfF4pfY7aPECnZJHiw0YsY_AF7WRoNnB1PuFGnJ6npg/export?format=csv"
PRODUCTS_URL = "https://docs.google.com/spreadsheets/d/1LfF4pfY7aPECnZJHiw0YsY_AF7WRoNnB1PuFGnJ6npg/export?format=csv&gid=2125665780"
STORES_URL =  "https://docs.google.com/spreadsheets/d/1LfF4pfY7aPECnZJHiw0YsY_AF7WRoNnB1PuFGnJ6npg/export?format=csv&gid=1763900964"

inventory = pd.read_csv(SHEET_URL)

inventory_csv = inventory.to_csv(index=False)

delivery_hash = hashlib.sha256(
    inventory_csv.encode("utf-8")
).hexdigest()
print(f"Inventory delivery SHA-256: {delivery_hash}")
# Load previously processed inventory deliveries
with open("delivery_history.json", "r") as file:
    delivery_history = json.load(file)

processed_deliveries = delivery_history["processed_deliveries"]
if delivery_hash in processed_deliveries:
    print("DUPLICATE DELIVERY DETECTED")
    print("Skipping previously processed inventory delivery.")
    sys.exit(0)
else:
    print("NEW DELIVERY DETECTED")
    
products = pd.read_csv(PRODUCTS_URL)
stores = pd.read_csv(STORES_URL)

stores["closed_at"] = pd.to_datetime(
    stores["closed_at"],
    errors="coerce"
)
parsed_timestamp = pd.to_datetime(
    inventory["inventory_timestamp"],
    errors="coerce"
)
inventory_with_store = inventory.merge(
    stores[["store_id", "status", "closed_at"]],
    on="store_id",
    how="left"
)
inventory_with_store["inventory_timestamp"] = pd.to_datetime(
    inventory_with_store["inventory_timestamp"],
    errors="coerce"
)
inventory_after_closure = (
    inventory_with_store["closed_at"].notna()
    & (
        inventory_with_store["inventory_timestamp"]
        >= inventory_with_store["closed_at"]
    )
)
print("\nPRODUCT CATALOG:")
print(products.to_string(index=False))

print("\nSTORE CATALOG:")
print(stores.to_string(index=False))
#Validation Variables
duplicate_inventory = inventory.duplicated(
    subset=[
        "store_id",
        "sku",
        "quantity_on_hand",
        "inventory_timestamp"
    ],
    keep=False
)
unknown_store = ~inventory["store_id"].isin(stores["store_id"])
invalid_timestamp = parsed_timestamp.isna()
invalid_quantity = inventory["quantity_on_hand"] < 0
missing_sku = inventory["sku"].isna()
unknown_sku = (
    inventory["sku"].notna()
    & ~inventory["sku"].isin(products["sku"])
)

conflicting_inventory = (
    inventory.groupby(
        ["store_id", "sku", "inventory_timestamp"]
    )["quantity_on_hand"]
    .transform("nunique") > 1
)

invalid_row = (
    invalid_quantity
    | missing_sku
    | unknown_sku
    | unknown_store
    | invalid_timestamp
    | duplicate_inventory
    | conflicting_inventory
    | inventory_after_closure
)
valid_inventory = inventory[~invalid_row]
rejected_inventory = inventory[invalid_row]
rejected_inventory = rejected_inventory.copy()
rejected_inventory["rejection_reason"] = ""

#Rejection Rules

rejected_inventory.loc[
    rejected_inventory.index.isin(
        inventory[conflicting_inventory].index
    ),
    "rejection_reason"
] = "CONFLICTING_INVENTORY_RECORD"

rejected_inventory.loc[
    rejected_inventory["quantity_on_hand"] < 0,
    "rejection_reason"
] = "NEGATIVE_QUANTITY"

rejected_inventory.loc[
    rejected_inventory["sku"].isna(),
    "rejection_reason"
] = "MISSING_SKU"

rejected_inventory.loc[
    rejected_inventory["sku"].notna()
    & ~rejected_inventory["sku"].isin(products["sku"]),
    "rejection_reason"
] = "UNKNOWN_SKU"

rejected_inventory.loc[
    ~rejected_inventory["store_id"].isin(stores["store_id"]),
    "rejection_reason"
] = "UNKNOWN_STORE"

rejected_inventory.loc[
    pd.to_datetime(
        rejected_inventory["inventory_timestamp"],
        errors="coerce"
    ).isna(),
    "rejection_reason"
] = "INVALID_TIMESTAMP"

rejected_inventory.loc[
    rejected_inventory.index.isin(
        inventory_with_store[inventory_after_closure].index
    ),
    "rejection_reason"
] = "INVENTORY_AFTER_STORE_CLOSURE"

print("VALID INVENTORY:")
print(valid_inventory.to_string(index=False))
print("\nREJECTED INVENTORY:")
print(rejected_inventory.to_string(index=False))
print("\nROWS WITH MISSING SKU:")
print(inventory[missing_sku].to_string(index=False))
print("\nROWS WITH UNKNOWN SKU:")
print(inventory[unknown_sku].to_string(index=False))
print("\nROWS WITH UNKNOWN STORE:")
print(inventory[unknown_store].to_string(index=False))
print("\nROWS WITH INVALID TIMESTAMP:")
print(inventory[invalid_timestamp].to_string(index=False))
print("\nDUPLICATE INVENTORY RECORDS:")
print(inventory[duplicate_inventory].to_string(index=False))
print("\nCONFLICTING INVENTORY RECORDS:")
print(inventory[conflicting_inventory].to_string(index=False))
print("\nINVENTORY WITH STORE STATUS:")
print(inventory_with_store.to_string(index=False))
print("\nINVENTORY AFTER STORE CLOSURE:")
print(
    inventory_with_store[inventory_after_closure]
    .to_string(index=False)
)