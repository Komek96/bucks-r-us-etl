"""Reusable data-loading utilities for analytics reports."""

from pathlib import Path

import pandas as pd


def load_report(report_path: str | Path) -> pd.DataFrame:
    """Load a generated analytics CSV report.

    Raises:
        FileNotFoundError: If the report does not exist.
        ValueError: If the CSV contains no column headers.
    """
    path = Path(report_path)

    if not path.is_file():
        raise FileNotFoundError(
            f"Analytics report not found: {path}"
        )

    try:
        return pd.read_csv(path)
    except pd.errors.EmptyDataError as exc:
        raise ValueError(
            f"Analytics report has no column headers: {path}"
        ) from exc
