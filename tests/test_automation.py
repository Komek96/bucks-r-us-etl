"""Tests for the Bucks-R-Us automation runner."""

from pathlib import Path

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


def test_duplicate_delivery_still_generates_reports(monkeypatch):
    """A successfully skipped duplicate must not block reporting."""
    calls = []

    def fake_run(command, **kwargs):
        calls.append(command)

        if command[1:] == ["load_inventory.py"]:
            return subprocess.CompletedProcess(
                command,
                returncode=0,
                stdout="DUPLICATE DELIVERY DETECTED",
            )

        return subprocess.CompletedProcess(
            command,
            returncode=0,
        )

    monkeypatch.setattr(subprocess, "run", fake_run)
    monkeypatch.setattr(
        sys, "argv", ["run_pipeline.py"]
    )

    main()

    assert len(calls) == len(PIPELINE_STEPS)

    assert calls[-1][1:] == [
        "-m",
        "reports.run_all_reports",
    ]


@pytest.fixture
def isolated_pipeline_logger():
    """Ensure logging handlers do not leak between tests."""
    import logging

    logger = logging.getLogger("bucks_r_us.pipeline")

    from logging.handlers import RotatingFileHandler

    for handler in logger.handlers[:]:
        if (
            isinstance(handler, RotatingFileHandler)
            and Path(handler.baseFilename).name == "pipeline.log"
        ):
            logger.removeHandler(handler)
            handler.close()

    yield

    from logging.handlers import RotatingFileHandler

    for handler in logger.handlers[:]:
        if (
            isinstance(handler, RotatingFileHandler)
            and Path(handler.baseFilename).name == "pipeline.log"
        ):
            logger.removeHandler(handler)
            handler.close()


def test_pipeline_success_logging(
    monkeypatch, tmp_path, isolated_pipeline_logger
):
    import automation.run_pipeline as runner

    commands = []

    def fake_run(command, **kwargs):
        commands.append(command)
        return subprocess.CompletedProcess(command, 0)

    monkeypatch.setattr(runner, "BASE_DIR", tmp_path)
    monkeypatch.setattr(subprocess, "run", fake_run)
    monkeypatch.setattr(sys, "argv", ["run_pipeline.py"])

    runner.main()

    log_path = tmp_path / "logs" / "pipeline.log"

    assert log_path.is_file()

    log_contents = log_path.read_text(encoding="utf-8")

    assert "Pipeline started." in log_contents
    assert "Pipeline completed successfully." in log_contents
    assert len(commands) == 4

    for index, (name, _) in enumerate(
        runner.PIPELINE_STEPS, start=1
    ):
        assert f"Starting step {index}: {name}" in log_contents
        assert f"Completed step {index}: {name}" in log_contents


def test_pipeline_failure_logging(
    monkeypatch, tmp_path, isolated_pipeline_logger
):
    import automation.run_pipeline as runner

    commands = []

    def fake_run(command, **kwargs):
        commands.append(command)

        if command[1:] == ["load_stores.py"]:
            raise subprocess.CalledProcessError(1, command)

        return subprocess.CompletedProcess(command, 0)

    monkeypatch.setattr(runner, "BASE_DIR", tmp_path)
    monkeypatch.setattr(subprocess, "run", fake_run)
    monkeypatch.setattr(sys, "argv", ["run_pipeline.py"])

    with pytest.raises(subprocess.CalledProcessError):
        runner.main()

    log_path = tmp_path / "logs" / "pipeline.log"

    assert log_path.is_file()

    log_contents = log_path.read_text(encoding="utf-8")

    assert "Completed step 1: Load products" in log_contents
    assert "Pipeline failed during step 2: Load stores" in log_contents
    assert "CalledProcessError" in log_contents

    assert "Starting step 3" not in log_contents
    assert "Pipeline completed successfully." not in log_contents
    assert len(commands) == 2
