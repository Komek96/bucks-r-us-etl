from unittest.mock import patch

from reports import run_all_reports


def test_batch_runner_executes_reports_in_order(tmp_path, monkeypatch):
    (tmp_path / "003_third.sql").write_text("SELECT 3;")
    (tmp_path / "001_first.sql").write_text("SELECT 1;")
    (tmp_path / "002_second.sql").write_text("SELECT 2;")
    (tmp_path / "README.md").write_text("Documentation")

    monkeypatch.setattr(run_all_reports, "REPORTS_DIR", tmp_path)

    with patch.object(run_all_reports, "run_report") as mock_run:
        run_all_reports.main()

    assert [
        call.args[0]
        for call in mock_run.call_args_list
    ] == [
        "001_first.sql",
        "002_second.sql",
        "003_third.sql",
    ]
