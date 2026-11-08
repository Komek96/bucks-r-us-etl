"""Tests for the Bucks-R-Us automation runner."""

from pathlib import Path

import subprocess
import sys

import pytest

import automation.run_pipeline as runner
from automation.run_pipeline import main, PIPELINE_STEPS


def test_dry_run_does_not_execute_commands(monkeypatch, capsys):
    def forbidden_run(*args, **kwargs):
        raise AssertionError("Dry run executed a subprocess!")

    monkeypatch.setattr(runner, "run_logged_step", forbidden_run)
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

    monkeypatch.setattr(runner, "run_logged_step", fake_run)
    monkeypatch.setattr(sys, "argv", ["run_pipeline.py"])

    main()

    expected = [
        [sys.executable, *arguments]
        for _, arguments in PIPELINE_STEPS
    ]

    assert [command for command, _ in calls] == expected
    assert all(options["logger"] is not None for _, options in calls)


def test_pipeline_stops_when_step_fails(monkeypatch):
    calls = []

    def fake_run(command, **kwargs):
        calls.append(command)

        if len(calls) == 2:
            raise subprocess.CalledProcessError(1, command)

    monkeypatch.setattr(runner, "run_logged_step", fake_run)
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

    monkeypatch.setattr(runner, "run_logged_step", fake_run)
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
    monkeypatch.setattr(runner, "run_logged_step", fake_run)
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
    monkeypatch.setattr(runner, "run_logged_step", fake_run)
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


class _RecordingPipelineLogger:
    """Collect formatted pipeline messages for assertions."""

    def __init__(self):
        self.messages = []

    def info(self, format_string, *args):
        self.messages.append(format_string % args)


def test_logged_step_streams_stdout_and_stderr(
    monkeypatch, tmp_path, capsys
):
    """A subprocess must write to both the terminal and logger."""
    import automation.run_pipeline as runner

    monkeypatch.setattr(runner, "BASE_DIR", tmp_path)

    logger = _RecordingPipelineLogger()

    command = [
        sys.executable,
        "-c",
        (
            "import sys; "
            "print('STDOUT_MARKER', flush=True); "
            "print('STDERR_MARKER', file=sys.stderr, flush=True)"
        ),
    ]

    runner.run_logged_step(command, logger)

    terminal_output = capsys.readouterr().out

    assert "STDOUT_MARKER" in terminal_output
    assert "STDERR_MARKER" in terminal_output

    assert any(
        "STDOUT_MARKER" in message
        for message in logger.messages
    )
    assert any(
        "STDERR_MARKER" in message
        for message in logger.messages
    )

    assert all(
        message.startswith("SUBPROCESS | ")
        for message in logger.messages
    )
    assert all(
        not message.endswith(("\n", "\r"))
        for message in logger.messages
    )


def test_logged_step_preserves_output_on_failure(
    monkeypatch, tmp_path, capsys
):
    """Failure output must be logged and the exit code preserved."""
    import automation.run_pipeline as runner

    monkeypatch.setattr(runner, "BASE_DIR", tmp_path)

    logger = _RecordingPipelineLogger()

    command = [
        sys.executable,
        "-c",
        (
            "import sys; "
            "print('FAILURE_MARKER', flush=True); "
            "sys.exit(7)"
        ),
    ]

    with pytest.raises(
        subprocess.CalledProcessError
    ) as error:
        runner.run_logged_step(command, logger)

    assert error.value.returncode == 7
    assert error.value.cmd == command

    terminal_output = capsys.readouterr().out

    assert "FAILURE_MARKER" in terminal_output
    assert any(
        "FAILURE_MARKER" in message
        for message in logger.messages
    )


def test_secure_log_permissions_and_repair(
    monkeypatch, tmp_path, isolated_pipeline_logger
):
    """New logs must be private and insecure permissions repaired."""
    import stat
    import automation.run_pipeline as runner

    monkeypatch.setattr(runner, "BASE_DIR", tmp_path)

    def permissions(path):
        return stat.S_IMODE(path.stat().st_mode)

    logger = runner.configure_pipeline_logger()
    log_dir = tmp_path / "logs"
    log_file = log_dir / "pipeline.log"

    assert permissions(log_dir) == 0o700
    assert permissions(log_file) == 0o600

    # Close our file handler before reopening the log.
    for handler in logger.handlers[:]:
        if isinstance(
            handler, runner.SecureRotatingFileHandler
        ):
            logger.removeHandler(handler)
            handler.close()

    # Deliberately weaken permissions inside tmp_path only.
    log_dir.chmod(0o777)
    log_file.chmod(0o666)

    runner.configure_pipeline_logger()

    assert permissions(log_dir) == 0o700
    assert permissions(log_file) == 0o600


def test_secure_log_rotation_permissions(
    monkeypatch, tmp_path, isolated_pipeline_logger
):
    """Rotating log files must remain owner-readable only."""
    import stat
    import automation.run_pipeline as runner

    monkeypatch.setattr(runner, "BASE_DIR", tmp_path)

    logger = runner.configure_pipeline_logger()

    handler = next(
        handler
        for handler in logger.handlers
        if isinstance(
            handler, runner.SecureRotatingFileHandler
        )
    )

    handler.maxBytes = 200
    handler.backupCount = 3

    for index in range(30):
        logger.info(
            "ROTATION_TEST_%02d %s",
            index,
            "X" * 60,
        )

    handler.flush()

    log_files = list(
        (tmp_path / "logs").glob("pipeline.log*")
    )

    assert len(log_files) >= 2

    for log_file in log_files:
        permissions = stat.S_IMODE(
            log_file.stat().st_mode
        )

        assert permissions == 0o600, (
            f"{log_file.name} has permissions "
            f"{oct(permissions)}"
        )
