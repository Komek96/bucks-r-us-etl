"""Orchestrate the Bucks-R-Us ETL and analytics pipeline."""

import argparse
import logging
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


def configure_pipeline_logger():
    """Configure rotating operational logs."""
    log_dir = BASE_DIR / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)

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
        handler = RotatingFileHandler(
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
            subprocess.run(
                command,
                cwd=BASE_DIR,
                check=True,
            )
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
