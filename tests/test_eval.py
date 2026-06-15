import json

from redaktsafe.cli import main
from redaktsafe.eval import run_eval


def test_eval_harness_reports_required_metrics(tmp_path):
    result = run_eval("evals/cases.jsonl", tmp_path)

    assert result["case_count"] == 10
    assert "recall" in result
    assert "precision" in result
    assert "false_positive_count" in result
    assert "unsafe_pass_count" in result
    assert "latency_ms_p50" in result
    assert "artifact_completeness_rate" in result
    assert "receipt_completeness_rate" in result
    assert "no_raw_input_violations" in result
    assert result["unsafe_pass_count"] == 0
    assert (tmp_path / "eval_results.json").exists()
    assert (tmp_path / "eval_report.md").exists()


def test_eval_cli_writes_results_and_report(tmp_path):
    status = main(["eval", "--fixtures", "evals/cases.jsonl", "--out", str(tmp_path)])

    assert status == 0
    results = json.loads((tmp_path / "eval_results.json").read_text(encoding="utf-8"))
    report = (tmp_path / "eval_report.md").read_text(encoding="utf-8")
    assert results["unsafe_pass_count"] == 0
    assert "recall" in report
    assert "precision" in report
    assert "false positives" in report
    assert "unsafe-pass count" in report
    assert "latency" in report
    assert "receipt completeness" in report
    assert "no-raw-input violations" in report

