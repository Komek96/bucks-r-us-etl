"""Tests for the Bucks-R-Us automation runner."""

import subprocess
import sys

import pytest

from automation.run_pipeline import main, PIPELINE_STEPS


def test_dry_run_does_not_execute_commands(monkeypatch, capsys):
    def forbidden_run(*args, **kwargs):
        raise AssertionError("Dry run executed a subprocess!")

    monkeypatch.setattr(subprocess, "run", forbidden_run)
    monkeypatch.setattr(
        sys, "argv", ["run_pipeline.py", "--dry-run"]
    )

    main()

    output = capsys.readouterr().out
    assert output.count("DRY RUN: Not executed.") == 4


def test_pipeline_executes_steps_in_order(monkeypatch):
    calls = []

    def fake_run(command, **kwargs):
        calls.append((command, kwargs))

    monkeypatch.setattr(subprocess, "run", fake_run)
    monkeypatch.setattr(sys, "argv", ["run_pipeline.py"])

    main()

    expected = [
        [sys.executable, *arguments]
        for _, arguments in PIPELINE_STEPS
    ]

    assert [command for command, _ in calls] == expected
    assert all(options["check"] is True for _, options in calls)


def test_pipeline_stops_when_step_fails(monkeypatch):
    calls = []

    def fake_run(command, **kwargs):
        calls.append(command)

        if len(calls) == 2:
            raise subprocess.CalledProcessError(1, command)

    monkeypatch.setattr(subprocess, "run", fake_run)
    monkeypatch.setattr(sys, "argv", ["run_pipeline.py"])

    with pytest.raises(subprocess.CalledProcessError):
        main()

    assert len(calls) == 2
    assert calls[-1][1:] == ["load_stores.py"]
