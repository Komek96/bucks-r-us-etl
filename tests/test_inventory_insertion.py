"""Tests for PostgreSQL inventory insertion."""

from unittest.mock import MagicMock, patch

import pandas as pd

from load_inventory import insert_inventory_records


def test_successful_inventory_insert():
    """A successful insert increments the inserted count."""

    inventory = pd.DataFrame({
        "store_id": ["BRU-0001"],
        "sku": ["SKU-20481"],
        "quantity_on_hand": [12],
        "inventory_timestamp": pd.to_datetime(
            ["2026-10-05 08:00:00"]
        ),
    })

    connection = MagicMock()
    cursor = (
        connection.__enter__.return_value
        .cursor.return_value.__enter__.return_value
    )

    cursor.rowcount = 1

    with patch("load_inventory.get_connection", return_value=connection):
        inserted, skipped = insert_inventory_records(
            inventory, "test-delivery-hash"
        )

    assert (inserted, skipped) == (1, 0)

    assert cursor.execute.call_count == 2

    inventory_query = cursor.execute.call_args_list[0]
    assert "INSERT INTO inventory" in inventory_query.args[0]
    assert inventory_query.args[1][0:3] == (
        "BRU-0001", "SKU-20481", 12
    )

    history_query = cursor.execute.call_args_list[1]
    assert "INSERT INTO delivery_history" in history_query.args[0]
    assert history_query.args[1] == (
        "test-delivery-hash", 1, 0
    )


def test_existing_inventory_record_is_skipped():
    """A conflicting inventory record increments the skipped count."""

    inventory = pd.DataFrame({
        "store_id": ["BRU-0001"],
        "sku": ["SKU-20481"],
        "quantity_on_hand": [12],
        "inventory_timestamp": pd.to_datetime(
            ["2026-10-05 08:00:00"]
        ),
    })

    connection = MagicMock()
    cursor = (
        connection.__enter__.return_value
        .cursor.return_value.__enter__.return_value
    )

    cursor.rowcount = 0

    with patch("load_inventory.get_connection", return_value=connection):
        inserted, skipped = insert_inventory_records(
            inventory, "existing-inventory-delivery"
        )

    assert (inserted, skipped) == (0, 1)

    assert cursor.execute.call_count == 2

    inventory_query = cursor.execute.call_args_list[0]
    assert "ON CONFLICT" in inventory_query.args[0]
    assert "DO NOTHING" in inventory_query.args[0]

    history_query = cursor.execute.call_args_list[1]
    assert "INSERT INTO delivery_history" in history_query.args[0]
    assert history_query.args[1] == (
        "existing-inventory-delivery", 0, 1
    )


def test_mixed_inventory_inserts_and_skips():
    """A mixed delivery must count inserted and skipped records correctly."""

    inventory = pd.DataFrame({
        "store_id": ["BRU-0001", "BRU-0001", "BRU-0002"],
        "sku": ["SKU-20481", "SKU-20482", "SKU-20483"],
        "quantity_on_hand": [12, 8, 20],
        "inventory_timestamp": pd.to_datetime([
            "2026-10-05 08:00:00",
            "2026-10-05 08:00:00",
            "2026-10-05 08:00:00",
        ]),
    })

    connection = MagicMock()
    cursor = (
        connection.__enter__.return_value
        .cursor.return_value.__enter__.return_value
    )

    # Simulate two inserts and one conflict.
    type(cursor).rowcount = property(
        lambda self: [1, 0, 1, 1][self.execute.call_count - 1]
    )

    with patch("load_inventory.get_connection", return_value=connection):
        inserted, skipped = insert_inventory_records(
            inventory, "mixed-delivery-hash"
        )

    assert (inserted, skipped) == (2, 1)
    assert cursor.execute.call_count == 4

    history_query = cursor.execute.call_args_list[3]
    assert "INSERT INTO delivery_history" in history_query.args[0]
    assert history_query.args[1] == ("mixed-delivery-hash", 2, 1)


def test_inventory_insert_propagates_database_failure():
    """A failed inventory insert must propagate its database error."""

    import pytest

    inventory = pd.DataFrame({
        "store_id": ["BRU-0001", "BRU-0002"],
        "sku": ["SKU-20481", "SKU-20482"],
        "quantity_on_hand": [12, 8],
        "inventory_timestamp": pd.to_datetime([
            "2026-10-05 08:00:00",
            "2026-10-05 08:00:00",
        ]),
    })

    connection = MagicMock()
    cursor = (
        connection.__enter__.return_value
        .cursor.return_value.__enter__.return_value
    )

    cursor.rowcount = 1
    cursor.execute.side_effect = [
        None,
        RuntimeError("Simulated PostgreSQL insertion failure"),
    ]

    with patch("load_inventory.get_connection", return_value=connection):
        with pytest.raises(
            RuntimeError,
            match="Simulated PostgreSQL insertion failure"
        ):
            insert_inventory_records(
                inventory, "failed-delivery-hash"
            )

    assert cursor.execute.call_count == 2

    # The delivery history must not be registered after the failure.
    assert all(
        "INSERT INTO delivery_history" not in call.args[0]
        for call in cursor.execute.call_args_list
    )

    # The connection context manager receives the exception.
    assert connection.__exit__.call_count == 1
    assert connection.__exit__.call_args.args[0] is RuntimeError
