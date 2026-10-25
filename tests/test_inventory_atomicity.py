"""Integration tests for atomic inventory delivery processing."""

import os
from unittest.mock import patch

import pandas as pd
import psycopg
import pytest

from load_inventory import insert_inventory_records


def test_delivery_history_failure_rolls_back_inventory():
    """Inventory must roll back if delivery registration fails."""

    connection_args = {
        "host": os.getenv("POSTGRES_HOST", "127.0.0.1"),
        "port": os.getenv("POSTGRES_PORT", "5432"),
        "dbname": "bucks_r_us_rollback_test",
        "user": os.getenv("POSTGRES_USER", "bru_user"),
        "password": os.environ["POSTGRES_PASSWORD"],
    }

    store_id = "BRU-0001"
    sku = "SKU-10025"
    timestamp = pd.Timestamp("2099-12-31 23:59:59")

    inventory = pd.DataFrame({
        "store_id": [store_id],
        "sku": [sku],
        "quantity_on_hand": [42],
        "inventory_timestamp": [timestamp],
    })

    invalid_hash = "X" * 65

    with psycopg.connect(**connection_args) as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT COUNT(*) FROM inventory
                WHERE store_id = %s
                  AND sku = %s
                  AND inventory_timestamp = %s
                """,
                (store_id, sku, timestamp.to_pydatetime()),
            )
            assert cursor.fetchone()[0] == 0, (
                "Test inventory record already exists."
            )

    with patch(
        "load_inventory.get_connection",
        side_effect=lambda: psycopg.connect(**connection_args),
    ):
        with pytest.raises(psycopg.errors.StringDataRightTruncation):
            insert_inventory_records(inventory, invalid_hash)

    with psycopg.connect(**connection_args) as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT COUNT(*) FROM inventory
                WHERE store_id = %s
                  AND sku = %s
                  AND inventory_timestamp = %s
                """,
                (store_id, sku, timestamp.to_pydatetime()),
            )
            remaining_inventory = cursor.fetchone()[0]

            cursor.execute(
                """
                SELECT COUNT(*) FROM delivery_history
                WHERE delivery_hash = %s
                """,
                (invalid_hash,),
            )
            remaining_history = cursor.fetchone()[0]

    assert remaining_inventory == 0
    assert remaining_history == 0
