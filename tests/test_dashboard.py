"""Tests for the Bucks-R-Us analytics dashboard."""


import pandas as pd
import pytest

from dashboard.data_loader import load_report


def test_load_report_valid_csv(tmp_path):
    report = tmp_path / "inventory.csv"
    report.write_text(
        "sku,quantity_on_hand\n"
        "SKU-001,12\n"
        "SKU-002,8\n",
        encoding="utf-8",
    )

    result = load_report(report)

    assert len(result) == 2
    assert list(result.columns) == [
        "sku",
        "quantity_on_hand",
    ]
    assert result["quantity_on_hand"].sum() == 20


def test_load_report_missing_file(tmp_path):
    missing = tmp_path / "missing.csv"

    with pytest.raises(FileNotFoundError):
        load_report(missing)


def test_load_report_completely_empty_csv(tmp_path):
    report = tmp_path / "empty.csv"
    report.write_text("", encoding="utf-8")

    with pytest.raises(ValueError, match="no column headers"):
        load_report(report)


def test_load_report_headers_only(tmp_path):
    report = tmp_path / "headers_only.csv"
    report.write_text(
        "sku,quantity_on_hand\n",
        encoding="utf-8",
    )

    result = load_report(report)

    assert isinstance(result, pd.DataFrame)
    assert result.empty
    assert list(result.columns) == [
        "sku",
        "quantity_on_hand",
    ]
