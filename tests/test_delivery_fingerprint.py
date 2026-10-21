"""Automated tests for inventory delivery fingerprints."""

import pandas as pd

from load_inventory import calculate_delivery_hash


def sample_inventory():
    """Create a synthetic inventory delivery."""
    return pd.DataFrame({
        "store_id": ["BRU-0001"],
        "sku": ["SKU-20481"],
        "quantity_on_hand": [12],
        "inventory_timestamp": ["2026-10-05 08:00:00"],
    })


def test_identical_deliveries_have_identical_hashes():
    """Identical deliveries must produce identical fingerprints."""
    inventory = sample_inventory()

    first_hash = calculate_delivery_hash(inventory)
    second_hash = calculate_delivery_hash(inventory.copy())

    assert first_hash == second_hash


def test_modified_delivery_has_different_hash():
    """Changing an inventory quantity must change the fingerprint."""
    inventory = sample_inventory()
    modified = inventory.copy()

    modified.loc[0, "quantity_on_hand"] = 25

    assert calculate_delivery_hash(inventory) != calculate_delivery_hash(modified)


def test_delivery_hash_has_valid_sha256_format():
    """SHA-256 fingerprints must contain 64 hexadecimal characters."""
    delivery_hash = calculate_delivery_hash(sample_inventory())

    assert len(delivery_hash) == 64
    assert all(character in "0123456789abcdef" for character in delivery_hash)
