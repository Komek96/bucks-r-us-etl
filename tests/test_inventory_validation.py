import pandas as pd

from extract_inventory import validate_inventory


def test_negative_inventory_quantity():
    """Reject negative quantities while preserving valid inventory."""

    products = pd.DataFrame({
        "sku": ["SKU-20481"],
    })

    stores = pd.DataFrame({
        "store_id": ["BRU-0001"],
        "status": ["active"],
        "closed_at": [None],
    })

    inventory = pd.DataFrame({
        "store_id": ["BRU-0001", "BRU-0001"],
        "sku": ["SKU-20481", "SKU-20481"],
        "quantity_on_hand": [12, -5],
        "inventory_timestamp": [
            "2026-10-05 08:00:00",
            "2026-10-06 08:00:00",
        ],
    })

    valid, rejected = validate_inventory(inventory, products, stores)

    assert len(valid) == 1
    assert len(rejected) == 1
    assert valid.iloc[0]["quantity_on_hand"] == 12
    assert rejected.iloc[0]["rejection_reason"] == "NEGATIVE_QUANTITY"


def test_unknown_product_sku():
    """Reject inventory referencing a product absent from the catalog."""

    products = pd.DataFrame({
        "sku": ["SKU-20481"],
    })

    stores = pd.DataFrame({
        "store_id": ["BRU-0001"],
        "status": ["active"],
        "closed_at": [None],
    })

    inventory = pd.DataFrame({
        "store_id": ["BRU-0001", "BRU-0001"],
        "sku": ["SKU-20481", "SKU-99999"],
        "quantity_on_hand": [12, 5],
        "inventory_timestamp": [
            "2026-10-05 08:00:00",
            "2026-10-05 08:00:00",
        ],
    })

    valid, rejected = validate_inventory(inventory, products, stores)

    assert len(valid) == 1
    assert len(rejected) == 1
    assert valid.iloc[0]["sku"] == "SKU-20481"
    assert rejected.iloc[0]["sku"] == "SKU-99999"
    assert rejected.iloc[0]["rejection_reason"] == "UNKNOWN_SKU"


def test_unknown_store_id():
    """Reject inventory referencing a store absent from the catalog."""

    products = pd.DataFrame({
        "sku": ["SKU-20481"],
    })

    stores = pd.DataFrame({
        "store_id": ["BRU-0001"],
        "status": ["active"],
        "closed_at": [None],
    })

    inventory = pd.DataFrame({
        "store_id": ["BRU-0001", "BRU-9999"],
        "sku": ["SKU-20481", "SKU-20481"],
        "quantity_on_hand": [12, 5],
        "inventory_timestamp": [
            "2026-10-05 08:00:00",
            "2026-10-05 08:00:00",
        ],
    })

    valid, rejected = validate_inventory(inventory, products, stores)

    assert len(valid) == 1
    assert len(rejected) == 1
    assert valid.iloc[0]["store_id"] == "BRU-0001"
    assert rejected.iloc[0]["store_id"] == "BRU-9999"
    assert rejected.iloc[0]["rejection_reason"] == "UNKNOWN_STORE"


def test_missing_product_sku():
    """Reject inventory records with a missing product SKU."""

    products = pd.DataFrame({
        "sku": ["SKU-20481"],
    })

    stores = pd.DataFrame({
        "store_id": ["BRU-0001"],
        "status": ["active"],
        "closed_at": [None],
    })

    inventory = pd.DataFrame({
        "store_id": ["BRU-0001", "BRU-0001"],
        "sku": ["SKU-20481", None],
        "quantity_on_hand": [12, 5],
        "inventory_timestamp": [
            "2026-10-05 08:00:00",
            "2026-10-06 08:00:00",
        ],
    })

    valid, rejected = validate_inventory(inventory, products, stores)

    assert len(valid) == 1
    assert len(rejected) == 1
    assert valid.iloc[0]["sku"] == "SKU-20481"
    assert pd.isna(rejected.iloc[0]["sku"])
    assert rejected.iloc[0]["rejection_reason"] == "MISSING_SKU"


def test_invalid_inventory_timestamp():
    """Reject inventory records with an unparseable timestamp."""

    products = pd.DataFrame({
        "sku": ["SKU-20481"],
    })

    stores = pd.DataFrame({
        "store_id": ["BRU-0001"],
        "status": ["active"],
        "closed_at": [None],
    })

    inventory = pd.DataFrame({
        "store_id": ["BRU-0001", "BRU-0001"],
        "sku": ["SKU-20481", "SKU-20481"],
        "quantity_on_hand": [12, 5],
        "inventory_timestamp": [
            "2026-10-05 08:00:00",
            "not-a-date",
        ],
    })

    valid, rejected = validate_inventory(inventory, products, stores)

    assert len(valid) == 1
    assert len(rejected) == 1
    assert valid.iloc[0]["inventory_timestamp"] == "2026-10-05 08:00:00"
    assert rejected.iloc[0]["inventory_timestamp"] == "not-a-date"
    assert rejected.iloc[0]["rejection_reason"] == "INVALID_TIMESTAMP"


def test_duplicate_inventory_records():
    """Reject both copies of an identical inventory record."""

    products = pd.DataFrame({
        "sku": ["SKU-20481"],
    })

    stores = pd.DataFrame({
        "store_id": ["BRU-0001"],
        "status": ["active"],
        "closed_at": [None],
    })

    inventory = pd.DataFrame({
        "store_id": ["BRU-0001", "BRU-0001"],
        "sku": ["SKU-20481", "SKU-20481"],
        "quantity_on_hand": [12, 12],
        "inventory_timestamp": [
            "2026-10-05 08:00:00",
            "2026-10-05 08:00:00",
        ],
    })

    valid, rejected = validate_inventory(inventory, products, stores)

    assert len(valid) == 0
    assert len(rejected) == 2
    assert rejected["quantity_on_hand"].tolist() == [12, 12]
    assert (
        rejected["rejection_reason"] == "DUPLICATE_INVENTORY_RECORD"
    ).all()


def test_conflicting_inventory_records():
    """Reject different quantities for the same store, SKU, and timestamp."""

    products = pd.DataFrame({
        "sku": ["SKU-20481"],
    })

    stores = pd.DataFrame({
        "store_id": ["BRU-0001"],
        "status": ["active"],
        "closed_at": [None],
    })

    inventory = pd.DataFrame({
        "store_id": ["BRU-0001", "BRU-0001", "BRU-0001"],
        "sku": ["SKU-20481", "SKU-20481", "SKU-20481"],
        "quantity_on_hand": [12, 25, 30],
        "inventory_timestamp": [
            "2026-10-05 08:00:00",
            "2026-10-05 08:00:00",
            "2026-10-06 08:00:00",
        ],
    })

    valid, rejected = validate_inventory(inventory, products, stores)

    assert len(valid) == 1
    assert len(rejected) == 2
    assert valid.iloc[0]["quantity_on_hand"] == 30
    assert set(rejected["quantity_on_hand"]) == {12, 25}
    assert (
        rejected["rejection_reason"] == "CONFLICTING_INVENTORY_RECORD"
    ).all()


def test_inventory_after_store_closure():
    """Reject inventory recorded after a store's closure timestamp."""

    products = pd.DataFrame({
        "sku": ["SKU-20481"],
    })

    stores = pd.DataFrame({
        "store_id": ["BRU-0001"],
        "status": ["closed"],
        "closed_at": ["2026-10-05 12:00:00"],
    })

    inventory = pd.DataFrame({
        "store_id": ["BRU-0001", "BRU-0001"],
        "sku": ["SKU-20481", "SKU-20481"],
        "quantity_on_hand": [12, 5],
        "inventory_timestamp": [
            "2026-10-04 08:00:00",
            "2026-10-06 08:00:00",
        ],
    })

    valid, rejected = validate_inventory(inventory, products, stores)

    assert len(valid) == 1
    assert len(rejected) == 1
    assert valid.iloc[0]["quantity_on_hand"] == 12
    assert rejected.iloc[0]["quantity_on_hand"] == 5
    assert (
        rejected.iloc[0]["rejection_reason"]
        == "INVENTORY_AFTER_STORE_CLOSURE"
    )
