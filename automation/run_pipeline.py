"""Orchestrate the Bucks-R-Us ETL and analytics pipeline."""

import argparse
import logging
import os
from logging.handlers import RotatingFileHandler
import subprocess
import sys
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent

PIPELINE_STEPS = [
    ("Load products", ["load_products.py"]),
    ("Load stores", ["load_stores.py"]),
    ("Load inventory", ["load_inventory.py"]),
    (
        "Generate analytics reports",
        ["-m", "reports.run_all_reports"],
    ),
]


class SecureRotatingFileHandler(RotatingFileHandler):
    """Create rotating log files with owner-only permissions."""

    def _open(self):
        flags = (
            os.O_WRONLY
            | os.O_CREAT
            | os.O_APPEND
            | getattr(os, "O_NOFOLLOW", 0)
        )

        descriptor = os.open(
            self.baseFilename,
            flags,
            0o600,
        )

        try:
            os.fchmod(descriptor, 0o600)

            return os.fdopen(
                descriptor,
                self.mode,
                encoding=self.encoding,
                errors=self.errors,
            )
        except Exception:
            os.close(descriptor)
            raise


def configure_pipeline_logger():
    """Configure rotating operational logs."""
    log_dir = BASE_DIR / "logs"
    log_dir.mkdir(
        parents=True,
        exist_ok=True,
        mode=0o700,
    )
    log_dir.chmod(0o700)

    logger = logging.getLogger("bucks_r_us.pipeline")
    logger.setLevel(logging.INFO)
    logger.propagate = False

    log_path = (log_dir / "pipeline.log").resolve()

    has_file_handler = any(
        isinstance(handler, RotatingFileHandler)
        and Path(handler.baseFilename) == log_path
        for handler in logger.handlers
    )

    if not has_file_handler:
        handler = SecureRotatingFileHandler(
            log_path,
            maxBytes=1_000_000,
            backupCount=3,
            encoding="utf-8",
        )

        handler.setFormatter(logging.Formatter(
            "%(asctime)s | %(levelname)s | %(message)s"
        ))

        logger.addHandler(handler)

    return logger


def run_logged_step(command, logger):
    """Stream subprocess output to the terminal and pipeline log."""
    with subprocess.Popen(
        command,
        cwd=BASE_DIR,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
    ) as process:
        for line in process.stdout:
            print(line, end="", flush=True)
            logger.info("SUBPROCESS | %s", line.rstrip("\r\n"))

        return_code = process.wait()

    if return_code != 0:
        raise subprocess.CalledProcessError(
            return_code,
            command,
        )


def main():
    parser = argparse.ArgumentParser(
        description="Run the Bucks-R-Us ETL pipeline."
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show commands without executing them.",
    )
    args = parser.parse_args()

    logger = (
        None if args.dry_run
        else configure_pipeline_logger()
    )

    if logger:
        logger.info("Pipeline started.")

    print("Bucks-R-Us ETL Pipeline", flush=True)

    for index, (name, arguments) in enumerate(
        PIPELINE_STEPS, start=1
    ):
        command = [sys.executable, *arguments]

        print(
            f"\nStep {index}: {name}",
            flush=True,
        )
        print(
            f"Command: {' '.join(command)}",
            flush=True,
        )

        if args.dry_run:
            print("DRY RUN: Not executed.", flush=True)
            continue

        if logger:
            logger.info("Starting step %d: %s", index, name)

        try:
            run_logged_step(command, logger=logger)
        except Exception:
            if logger:
                logger.exception(
                    "Pipeline failed during step %d: %s",
                    index,
                    name,
                )
            raise

        print(f"Completed: {name}", flush=True)

        if logger:
            logger.info("Completed step %d: %s", index, name)

    print(
        "\nPipeline dry run complete."
        if args.dry_run
        else "\nPipeline completed successfully.",
        flush=True,
    )


    if logger:
        logger.info("Pipeline completed successfully.")


if __name__ == "__main__":
    main()
