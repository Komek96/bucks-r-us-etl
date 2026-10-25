from reports.run_report import REPORTS_DIR, run_report


def main():
    report_files = sorted(REPORTS_DIR.glob("[0-9][0-9][0-9]_*.sql"))

    if not report_files:
        raise RuntimeError("No SQL analytics reports found.")

    print(f"Found {len(report_files)} SQL reports.")

    for report_path in report_files:
        print(f"\\nRunning {report_path.name}...")
        run_report(report_path.name)

    print(f"\\nCompleted {len(report_files)} reports.")


if __name__ == "__main__":
    main()
