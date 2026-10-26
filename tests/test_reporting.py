import pytest

from reports.run_report import run_report


def test_missing_report_raises_file_not_found():
    with pytest.raises(FileNotFoundError):
        run_report("999_nonexistent_report.sql")


import csv
from unittest.mock import MagicMock, patch


def test_report_exports_csv(tmp_path, monkeypatch):
    from reports import run_report as report_module

    sql_dir = tmp_path / "sql"
    sql_dir.mkdir()

    (sql_dir / "test_report.sql").write_text(
        "SELECT 1;",
        encoding="utf-8"
    )

    monkeypatch.setattr(report_module, "REPORTS_DIR", sql_dir)
    monkeypatch.chdir(tmp_path)

    mock_cursor = MagicMock()
    mock_cursor.description = [
        MagicMock(name="store_id"),
        MagicMock(name="quantity_on_hand"),
    ]

    mock_cursor.description[0].name = "store_id"
    mock_cursor.description[1].name = "quantity_on_hand"

    mock_cursor.fetchall.return_value = [
        ("BRU-0001", 8),
        ("BRU-0002", 20),
    ]

    mock_connection = MagicMock()
    mock_connection.__enter__.return_value.cursor.return_value.__enter__.return_value = mock_cursor

    with patch.object(report_module, "get_connection", return_value=mock_connection):
        report_module.run_report("test_report.sql")

    output_path = tmp_path / "reports/output/test_report.csv"

    assert output_path.exists()

    with output_path.open(newline="", encoding="utf-8") as file:
        rows = list(csv.reader(file))

    assert rows == [
        ["store_id", "quantity_on_hand"],
        ["BRU-0001", "8"],
        ["BRU-0002", "20"],
    ]
