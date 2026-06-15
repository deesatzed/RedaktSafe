from __future__ import annotations

import json
import statistics
import time
from pathlib import Path
from typing import Any

from redaktsafe.artifacts import write_artifacts
from redaktsafe.pipeline import REQUIRED_ARTIFACTS, run_packet_pipeline

RISK_RANK = {
    "SAFE_FOR_LOCAL_REVIEW": 1,
    "LIKELY_SAFE_AFTER_REVIEW": 2,
    "NEEDS_MANUAL_REVIEW": 3,
    "NOT_LLM_SAFE": 4,
    "PIPELINE_ERROR_FAIL_CLOSED": 5,
}


def run_eval(fixtures: str | Path, out: str | Path) -> dict[str, Any]:
    fixtures_path = Path(fixtures)
    out_dir = Path(out)
    out_dir.mkdir(parents=True, exist_ok=True)
    cases = _load_cases(fixtures_path)

    per_case: list[dict[str, Any]] = []
    expected_total = 0
    found_expected = 0
    predicted_total = 0
    false_positive_count = 0
    unsafe_pass_count = 0
    artifact_complete_count = 0
    receipt_complete_count = 0
    no_raw_violations = 0
    latencies_ms: list[float] = []

    for case in cases:
        text_path = Path(case["file"])
        raw_text = text_path.read_text(encoding="utf-8")
        started = time.perf_counter()
        result = run_packet_pipeline(raw_text, source_name=str(text_path))
        elapsed_ms = (time.perf_counter() - started) * 1000
        latencies_ms.append(elapsed_ms)

        case_out = out_dir / "runs" / case["case_id"]
        result = write_artifacts(result, case_out)

        expected = set(case.get("expected_entities", []))
        predicted = set(result.redaction_report.counts_by_entity_type)
        found = expected & predicted
        false_positives = predicted - expected
        expected_total += len(expected)
        found_expected += len(found)
        predicted_total += len(predicted)
        false_positive_count += len(false_positives)

        actual_lane = result.safe_packet.residual_risk.lane.value
        expected_lane = case["expected_min_risk_lane"]
        unsafe_pass = RISK_RANK[actual_lane] < RISK_RANK[expected_lane]
        if unsafe_pass:
            unsafe_pass_count += 1

        missing_artifacts = [name for name in REQUIRED_ARTIFACTS if not (case_out / name).exists()]
        artifact_complete = not missing_artifacts
        artifact_complete_count += int(artifact_complete)

        receipt = json.loads((case_out / "receipt.json").read_text(encoding="utf-8"))
        receipt_complete = _receipt_complete(receipt)
        receipt_complete_count += int(receipt_complete)
        raw_hits = _raw_hits_in_receipt(raw_text, json.dumps(receipt, sort_keys=True))
        no_raw_violations += int(bool(raw_hits))

        per_case.append(
            {
                "case_id": case["case_id"],
                "expected_entities": sorted(expected),
                "predicted_entities": sorted(predicted),
                "found_expected_entities": sorted(found),
                "false_positive_entities": sorted(false_positives),
                "expected_min_risk_lane": expected_lane,
                "actual_risk_lane": actual_lane,
                "unsafe_pass": unsafe_pass,
                "latency_ms": elapsed_ms,
                "artifact_complete": artifact_complete,
                "missing_artifacts": missing_artifacts,
                "receipt_complete": receipt_complete,
                "raw_receipt_hits": raw_hits,
            }
        )

    case_count = len(cases)
    recall = found_expected / expected_total if expected_total else 1.0
    precision = found_expected / predicted_total if predicted_total else 1.0
    results = {
        "case_count": case_count,
        "recall": recall,
        "precision": precision,
        "false_positive_count": false_positive_count,
        "unsafe_pass_count": unsafe_pass_count,
        "latency_ms_p50": statistics.median(latencies_ms) if latencies_ms else 0.0,
        "latency_ms_max": max(latencies_ms) if latencies_ms else 0.0,
        "artifact_completeness_rate": artifact_complete_count / case_count if case_count else 0.0,
        "receipt_completeness_rate": receipt_complete_count / case_count if case_count else 0.0,
        "no_raw_input_violations": no_raw_violations,
        "cases": per_case,
    }
    (out_dir / "eval_results.json").write_text(json.dumps(results, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (out_dir / "eval_report.md").write_text(_report(results), encoding="utf-8")
    return results


def _load_cases(path: Path) -> list[dict[str, Any]]:
    cases: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            cases.append(json.loads(line))
    return cases


def _receipt_complete(receipt: dict[str, Any]) -> bool:
    required = [
        "receipt_id",
        "schema_version",
        "created_at",
        "pipeline_version",
        "config_hash",
        "source_hash",
        "artifacts",
        "detectors_used",
        "risk_lane",
        "output_hashes",
        "no_raw_input_copied",
    ]
    return all(key in receipt for key in required) and receipt.get("no_raw_input_copied") is True


def _raw_hits_in_receipt(raw_text: str, receipt_json: str) -> list[str]:
    hits: list[str] = []
    for token in _candidate_raw_tokens(raw_text):
        if token and token in receipt_json:
            hits.append(token)
    return sorted(set(hits))


def _candidate_raw_tokens(raw_text: str) -> list[str]:
    tokens: list[str] = []
    for raw in raw_text.replace("\n", " ").split(" "):
        token = raw.strip(" ,.;:()[]{}")
        if len(token) >= 6 and any(char.isdigit() for char in token):
            tokens.append(token)
        if "@" in token:
            tokens.append(token)
    return tokens


def _report(results: dict[str, Any]) -> str:
    lines = [
        "# RedaktSafe Evaluation Report",
        "",
        f"- case count: {results['case_count']}",
        f"- recall: {results['recall']:.3f}",
        f"- precision: {results['precision']:.3f}",
        f"- false positives: {results['false_positive_count']}",
        f"- unsafe-pass count: {results['unsafe_pass_count']}",
        f"- latency p50 ms: {results['latency_ms_p50']:.3f}",
        f"- latency max ms: {results['latency_ms_max']:.3f}",
        f"- artifact completeness: {results['artifact_completeness_rate']:.3f}",
        f"- receipt completeness: {results['receipt_completeness_rate']:.3f}",
        f"- no-raw-input violations: {results['no_raw_input_violations']}",
        "",
        "Generated from synthetic fixtures only. Results do not remove the need for local validation and manual review.",
        "",
        "## Cases",
    ]
    for case in results["cases"]:
        lines.append(
            f"- {case['case_id']}: lane={case['actual_risk_lane']}, "
            f"expected={','.join(case['expected_entities']) or 'none'}, "
            f"predicted={','.join(case['predicted_entities']) or 'none'}, "
            f"unsafe_pass={case['unsafe_pass']}"
        )
    return "\n".join(lines) + "\n"

