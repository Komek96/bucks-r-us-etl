"""Tests for PostgreSQL delivery fingerprint lookups."""

from unittest.mock import MagicMock, patch

from load_inventory import delivery_exists


def mock_database(count):
    """Create a mocked PostgreSQL connection and cursor."""
    connection = MagicMock()
    cursor = connection.__enter__.return_value.cursor.return_value.__enter__.return_value
    cursor.fetchone.return_value = (count,)
    return connection, cursor


def test_new_delivery_not_found():
    """A new delivery should have zero matching fingerprints."""
    connection, _ = mock_database(0)

    with patch("load_inventory.get_connection", return_value=connection):
        assert delivery_exists("new-delivery-hash") == 0


def test_existing_delivery_found():
    """An existing delivery should have one matching fingerprint."""
    connection, _ = mock_database(1)

    with patch("load_inventory.get_connection", return_value=connection):
        assert delivery_exists("existing-delivery-hash") == 1


def test_delivery_lookup_uses_parameterized_query():
    """The fingerprint must be passed as a SQL parameter."""
    connection, cursor = mock_database(0)
    fingerprint = "a" * 64

    with patch("load_inventory.get_connection", return_value=connection):
        delivery_exists(fingerprint)

    cursor.execute.assert_called_once_with(
        "SELECT COUNT(*) FROM delivery_history WHERE delivery_hash = %s",
        (fingerprint,)
    )
