"""Tests ensuring the inventory loader is safe to import."""

import subprocess
import sys


def test_loader_import_has_no_etl_side_effects():
    """Importing the loader must not download data or connect to PostgreSQL."""

    script = """
from unittest.mock import patch

def forbidden(*args, **kwargs):
    raise AssertionError("ETL operation attempted during import")

with patch("pandas.read_csv", side_effect=forbidden), \\
     patch("database.get_connection", side_effect=forbidden):
    import load_inventory

assert callable(load_inventory.main)
"""

    result = subprocess.run(
        [sys.executable, "-c", script],
        capture_output=True,
        text=True,
        timeout=15,
        check=False,
    )

    assert result.returncode == 0, (
        f"Loader import failed:\n{result.stdout}\n{result.stderr}"
    )
