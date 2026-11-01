"""Tests for historical store-closure protection."""

import runpy

import pandas as pd
import pytest

import database


class FakeCursor:
    def __init__(self, closed_store_ids):
        self.closed_store_ids = closed_store_ids
        self.executed = []

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def execute(self, sql, parameters=None):
        self.executed.append((sql, parameters))

    def fetchall(self):
        return [(store_id,) for store_id in self.closed_store_ids]


class FakeConnection:
    def __init__(self, cursor):
        self.fake_cursor = cursor

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def cursor(self):
        return self.fake_cursor


def run_store_loader(monkeypatch, status, closed_at, existing_closed):
    source = pd.DataFrame([{
        "store_id": "BRU-0002",
        "address": "123 Test Street",
        "city": "Glorpono",
        "state": "GP",
        "zip_code": "12345",
        "status": status,
        "closed_at": closed_at,
    }])

    cursor = FakeCursor(existing_closed)

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

    runpy.run_path("load_stores.py", run_name="__main__")

    return cursor


def test_previously_closed_store_cannot_reopen(monkeypatch):
    with pytest.raises(
        ValueError,
        match="Previously closed stores cannot be reopened",
    ):
        run_store_loader(
            monkeypatch,
            status="active",
            closed_at=None,
            existing_closed={"BRU-0002"},
        )


def test_active_store_can_transition_to_closed(monkeypatch):
    cursor = run_store_loader(
        monkeypatch,
        status="closed",
        closed_at="2026-10-01",
        existing_closed=set(),
    )

    inserts = [
        sql for sql, _ in cursor.executed
        if "INSERT INTO stores" in sql
    ]

    assert len(inserts) == 1


def assert_invalid_store_rejected(
    monkeypatch, closed_at, expected_message
):
    """Verify invalid source data cannot reach PostgreSQL."""

    source = pd.DataFrame([{
        "store_id": "BRU-0002",
        "address": "123 Test Street",
        "city": "Glorpono",
        "state": "GP",
        "zip_code": "12345",
        "status": "closed",
        "closed_at": closed_at,
    }])

    monkeypatch.setattr(
        pd,
        "read_csv",
        lambda *args, **kwargs: source.copy(),
    )

    def forbidden_connection():
        raise AssertionError(
            "Invalid store data attempted database access!"
        )

    monkeypatch.setattr(
        database,
        "get_connection",
        forbidden_connection,
    )

    with pytest.raises(ValueError, match=expected_message):
        runpy.run_path(
            "load_stores.py",
            run_name="__main__",
        )


@pytest.mark.parametrize(
    "bad_date",
    ["not-a-date", "2026-02-30"],
)
def test_malformed_closure_date_rejected_before_database_access(
    monkeypatch, bad_date
):
    assert_invalid_store_rejected(
        monkeypatch,
        closed_at=bad_date,
        expected_message="Invalid closed_at date",
    )


def test_closed_store_without_date_rejected_before_database_access(
    monkeypatch,
):
    assert_invalid_store_rejected(
        monkeypatch,
        closed_at=None,
        expected_message="Closed stores must have a closure date",
    )
