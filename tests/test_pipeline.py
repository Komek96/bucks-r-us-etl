import os
import psycopg


def test_postgresql_connection():
    """Verify access to the isolated rollback test database."""
    with psycopg.connect(
        host=os.getenv("POSTGRES_HOST", "127.0.0.1"),
        port=os.getenv("POSTGRES_PORT", "5432"),
        dbname="bucks_r_us_rollback_test",
        user=os.getenv("POSTGRES_USER", "bru_user"),
        password=os.environ["POSTGRES_PASSWORD"],
    ) as conn:
        with conn.cursor() as cursor:
            cursor.execute("SELECT current_database();")
            database_name = cursor.fetchone()[0]

    assert database_name == "bucks_r_us_rollback_test"


def test_transaction_rollback():
    """Verify that an exception rolls back an inventory insert."""
    test_sku = "SKU-10025"
    test_store = "BRU-0001"
    test_timestamp = "2099-01-01 08:00:00"

    connection_args = {
        "host": os.getenv("POSTGRES_HOST", "127.0.0.1"),
        "port": os.getenv("POSTGRES_PORT", "5432"),
        "dbname": "bucks_r_us_rollback_test",
        "user": os.getenv("POSTGRES_USER", "bru_user"),
        "password": os.environ["POSTGRES_PASSWORD"],
    }

    with psycopg.connect(**connection_args) as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT COUNT(*)
                FROM inventory
                WHERE store_id = %s
                  AND sku = %s
                  AND inventory_timestamp = %s;
                """,
                (test_store, test_sku, test_timestamp),
            )
            assert cursor.fetchone()[0] == 0, (
                "Rollback test record already exists."
            )

    try:
        with psycopg.connect(**connection_args) as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO inventory (
                        store_id, sku, quantity_on_hand, inventory_timestamp
                    )
                    VALUES (%s, %s, %s, %s);
                    """,
                    (test_store, test_sku, 999, test_timestamp),
                )

                raise RuntimeError("CONTROLLED TEST FAILURE")

    except RuntimeError as error:
        assert str(error) == "CONTROLLED TEST FAILURE"
    else:
        raise AssertionError("Expected controlled failure was not raised.")

    with psycopg.connect(**connection_args) as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT COUNT(*)
                FROM inventory
                WHERE store_id = %s
                  AND sku = %s
                  AND inventory_timestamp = %s;
                """,
                (test_store, test_sku, test_timestamp),
            )
            remaining_records = cursor.fetchone()[0]

    assert remaining_records == 0
