import pandas as pd

SHEET_URL = "https://docs.google.com/spreadsheets/d/1LfF4pfY7aPECnZJHiw0YsY_AF7WRoNnB1PuFGnJ6npg/export?format=csv"
PRODUCTS_URL = "https://docs.google.com/spreadsheets/d/1LfF4pfY7aPECnZJHiw0YsY_AF7WRoNnB1PuFGnJ6npg/export?format=csv&gid=2125665780"
STORES_URL =  "https://docs.google.com/spreadsheets/d/1LfF4pfY7aPECnZJHiw0YsY_AF7WRoNnB1PuFGnJ6npg/export?format=csv&gid=1763900964"

inventory = pd.read_csv(SHEET_URL)
products = pd.read_csv(PRODUCTS_URL)
stores = pd.read_csv(STORES_URL)
parsed_timestamp = pd.to_datetime(
    inventory["inventory_timestamp"],
    errors="coerce"
)

print("\nPRODUCT CATALOG:")
print(products.to_string(index=False))

print("\nSTORE CATALOG:")
print(stores.to_string(index=False))
#Validation Variables
duplicate_inventory = inventory.duplicated(
    subset=["store_id", "sku", "inventory_timestamp"],
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
invalid_row = (
    invalid_quantity
    | missing_sku
    | unknown_sku
    | unknown_store
    | invalid_timestamp
    | duplicate_inventory
)
invalid_timestamp = parsed_timestamp.isna()
valid_inventory = inventory[~invalid_row]
rejected_inventory = inventory[invalid_row]
rejected_inventory = rejected_inventory.copy()
rejected_inventory["rejection_reason"] = ""

#Rejection Rules

conflicting_inventory = (
    inventory.groupby(
        ["store_id", "sku", "inventory_timestamp"]
    )["quantity_on_hand"]
    .transform("nunique") > 1
)

duplicate_inventory = inventory.duplicated(
    subset=[
        "store_id",
        "sku",
        "quantity_on_hand",
        "inventory_timestamp"
    ],
    keep=False
)

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
    rejected_inventory.duplicated(
        subset=[
            "store_id",
            "sku",
            "quantity_on_hand",
            "inventory_timestamp"
        ],
        keep=False
    ),
    "rejection_reason"
] = "DUPLICATE_INVENTORY_RECORD"

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