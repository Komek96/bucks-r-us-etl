"""Tests for historical store closure-date protection."""

from datetime import datetime
import runpy

import pandas as pd
import pytest

import database


class FakeCursor:
    def __init__(self):
        self.queries = []
        self.last_sql = ""

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def execute(self, sql, parameters=None):
        self.last_sql = sql
        self.queries.append((sql, parameters))

    def fetchall(self):
        if "SELECT store_id, closed_at" in self.last_sql:
            return [
                ("BRU-0002", datetime(2026, 10, 1))
            ]

        if "SELECT store_id" in self.last_sql:
            return [("BRU-0002",)]

        raise AssertionError("Unexpected fetchall() call")


class FakeConnection:
    def __init__(self, cursor):
        self.test_cursor = cursor

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def cursor(self):
        return self.test_cursor


def run_loader_with_closure_date(monkeypatch, closure_date):
    source = pd.DataFrame([{
        "store_id": "BRU-0002",
        "address": "123 Test Street",
        "city": "Glorpono",
        "state": "GP",
        "zip_code": "12345",
        "status": "closed",
        "closed_at": closure_date,
    }])

    cursor = FakeCursor()

    monkeypatch.setattr(
        pd,
        "read_csv",
        lambda *args, **kwargs: source.copy(),
    )

    monkeypatch.setattr(
        database,
        "get_connection",
        lambda: FakeConnection(cursor),
    )

    return cursor


def test_changed_historical_closure_date_is_rejected(monkeypatch):
    cursor = run_loader_with_closure_date(
        monkeypatch,
        "2026-10-15",
    )

    with pytest.raises(
        ValueError,
        match="Historical store closure date cannot be changed",
    ):
        runpy.run_path("load_stores.py", run_name="__main__")

    assert not any(
        "INSERT INTO stores" in sql
        for sql, _ in cursor.queries
    )


def test_unchanged_historical_closure_date_is_allowed(monkeypatch):
    cursor = run_loader_with_closure_date(
        monkeypatch,
        "2026-10-01",
    )

    runpy.run_path("load_stores.py", run_name="__main__")

    inserts = [
        (sql, parameters)
        for sql, parameters in cursor.queries
        if "INSERT INTO stores" in sql
    ]

    assert len(inserts) == 1
    assert inserts[0][1][0] == "BRU-0002"
    assert inserts[0][1][-1] == datetime(2026, 10, 1)
