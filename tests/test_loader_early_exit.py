"""Tests for the inventory loader's duplicate-delivery early exit."""

from unittest.mock import patch

import pandas as pd
import pytest

from load_inventory import main, SHEET_URL


def test_duplicate_delivery_exits_before_processing():
    """Duplicate deliveries must not proceed to validation or insertion."""

    inventory = pd.DataFrame({
        "store_id": ["BRU-0001"],
        "sku": ["SKU-20481"],
        "quantity_on_hand": [12],
        "inventory_timestamp": ["2026-10-05 08:00:00"],
    })

    with (
        patch("load_inventory.pd.read_csv", return_value=inventory) as read_csv,
        patch("load_inventory.delivery_exists", return_value=1) as lookup,
        patch("load_inventory.get_connection") as connection,
        patch("load_inventory.validate_inventory") as validation,
    ):
        with pytest.raises(SystemExit) as exit_info:
            main()

    assert exit_info.value.code == 0

    # Only the initial inventory download should occur.
    read_csv.assert_called_once_with(SHEET_URL)

    # The duplicate-delivery lookup must occur.
    lookup.assert_called_once()

    # No additional database connections or validation should occur.
    connection.assert_not_called()
    validation.assert_not_called()


def test_new_delivery_continues_to_validation():
    """A new delivery must download reference data and reach validation."""

    inventory = pd.DataFrame({
        "store_id": ["BRU-0001"],
        "sku": ["SKU-20481"],
        "quantity_on_hand": [12],
        "inventory_timestamp": ["2026-10-05 08:00:00"],
    })

    with (
        patch("load_inventory.pd.read_csv", return_value=inventory) as read_csv,
        patch("load_inventory.delivery_exists", return_value=0) as lookup,
        patch(
            "load_inventory.validate_inventory",
            side_effect=RuntimeError("VALIDATION_REACHED"),
        ) as validation,
        patch("load_inventory.get_connection") as connection,
    ):
        with pytest.raises(RuntimeError, match="VALIDATION_REACHED"):
            main()

    assert read_csv.call_count == 3
    lookup.assert_called_once()
    validation.assert_called_once()
    connection.assert_not_called()
