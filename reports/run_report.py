import csv
from pathlib import Path
import sys

from database import get_connection


REPORTS_DIR = Path(__file__).resolve().parent.parent / "sql" / "analytics"


def run_report(report_filename):
    report_path = REPORTS_DIR / report_filename

    if not report_path.is_file():
        raise FileNotFoundError(f"Report not found: {report_path}")

    sql = report_path.read_text(encoding="utf-8")

    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(sql)

            columns = [column.name for column in cursor.description]
            rows = cursor.fetchall()

    print(f"Report: {report_filename}")
    print(f"Columns: {', '.join(columns)}")
    print(f"Rows returned: {len(rows)}")

    output_dir = Path("reports/output")
    output_dir.mkdir(parents=True, exist_ok=True)

    output_path = output_dir / f"{Path(report_filename).stem}.csv"

    with output_path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(columns)
        writer.writerows(rows)

    print(f"CSV exported: {output_path}")

    return columns, rows


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python -m reports.run_report <report.sql>")
        sys.exit(1)

    run_report(sys.argv[1])
