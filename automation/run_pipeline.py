"""Orchestrate the Bucks-R-Us ETL and analytics pipeline."""

import argparse
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

        subprocess.run(
            command,
            cwd=BASE_DIR,
            check=True,
        )

        print(f"Completed: {name}", flush=True)

    print(
        "\nPipeline dry run complete."
        if args.dry_run
        else "\nPipeline completed successfully.",
        flush=True,
    )


if __name__ == "__main__":
    main()
