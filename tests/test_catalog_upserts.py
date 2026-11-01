"""PostgreSQL integration tests for catalog UPSERT statements."""

import ast
from datetime import datetime
import os
from pathlib import Path

import psycopg
import pytest


BASE_DIR = Path(__file__).resolve().parent.parent
TEST_DATABASE = "bucks_r_us_rollback_test"


def get_upsert_sql(filename, table):
    """Read the actual UPSERT SQL without executing loader code."""
    source = (BASE_DIR / filename).read_text(encoding="utf-8")
    tree = ast.parse(source)

    matches = [
        node.args[0].value
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "execute"
        and node.args
        and isinstance(node.args[0], ast.Constant)
        and isinstance(node.args[0].value, str)
        and f"INSERT INTO {table}" in node.args[0].value
    ]

    assert len(matches) == 1
    assert "ON CONFLICT" in matches[0]
    assert "DO UPDATE SET" in matches[0]

    return matches[0]


@pytest.fixture
def test_connection():
    """Use the isolated test database and always roll back."""
    assert TEST_DATABASE != "bucks_r_us"

    conn = psycopg.connect(
        host=os.getenv("POSTGRES_HOST", "127.0.0.1"),
        port=os.getenv("POSTGRES_PORT", "5432"),
        dbname=TEST_DATABASE,
        user=os.getenv("POSTGRES_USER", "bru_user"),
        password=os.environ["POSTGRES_PASSWORD"],
    )

    try:
        yield conn
    finally:
        try:
            conn.rollback()
        finally:
            conn.close()


def test_product_upsert_insert_update_and_noop(test_connection):
    sql = get_upsert_sql("load_products.py", "products")
    sku = "SKU-UPSERT-TEST"

    with test_connection.cursor() as cursor:
        cursor.execute(
            "SELECT COUNT(*) FROM products WHERE sku = %s",
            (sku,),
        )
        assert cursor.fetchone()[0] == 0

        initial = (
            sku, "Test Product", "Testing", "active"
        )

        cursor.execute(sql, initial)
        assert cursor.rowcount == 1

        updated = (
            sku, "Updated Test Product", "Testing", "inactive"
        )

        cursor.execute(sql, updated)
        assert cursor.rowcount == 1

        cursor.execute(sql, updated)
        assert cursor.rowcount == 0

        cursor.execute(
            """
            SELECT product_name, category, status
            FROM products
            WHERE sku = %s
            """,
            (sku,),
        )

        assert cursor.fetchone() == (
            "Updated Test Product", "Testing", "inactive"
        )

        cursor.execute(
            "SELECT COUNT(*) FROM products WHERE sku = %s",
            (sku,),
        )
        assert cursor.fetchone()[0] == 1


def test_store_upsert_insert_update_and_noop(test_connection):
    sql = get_upsert_sql("load_stores.py", "stores")
    store_id = "BRU-UPSERT-TEST"

    with test_connection.cursor() as cursor:
        cursor.execute(
            "SELECT COUNT(*) FROM stores WHERE store_id = %s",
            (store_id,),
        )
        assert cursor.fetchone()[0] == 0

        initial = (
            store_id,
            "123 Test Street",
            "Glorpono",
            "GP",
            "12345",
            "active",
            None,
        )

        cursor.execute(sql, initial)
        assert cursor.rowcount == 1

        closure_date = datetime(2026, 10, 1)

        updated = (
            store_id,
            "123 Test Street",
            "Glorpono",
            "GP",
            "12345",
            "closed",
            closure_date,
        )

        cursor.execute(sql, updated)
        assert cursor.rowcount == 1

        cursor.execute(sql, updated)
        assert cursor.rowcount == 0

        cursor.execute(
            """
            SELECT status, closed_at
            FROM stores
            WHERE store_id = %s
            """,
            (store_id,),
        )

        assert cursor.fetchone() == (
            "closed", closure_date
        )

        cursor.execute(
            "SELECT COUNT(*) FROM stores WHERE store_id = %s",
            (store_id,),
        )
        assert cursor.fetchone()[0] == 1
