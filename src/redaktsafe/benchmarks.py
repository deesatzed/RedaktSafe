from __future__ import annotations

import json
import re
import shutil
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from redaktsafe.eval import run_eval


@dataclass(frozen=True)
class BenchmarkSpec:
    benchmark_id: str
    name: str
    source_url: str
    access: str
    loader: str
    default_split: str
    notes: str


@dataclass(frozen=True)
class BenchmarkRecord:
    case_id: str
    text: str
    expected_entities: list[str]
    source_metadata: dict[str, str]


BENCHMARK_SPECS: dict[str, BenchmarkSpec] = {
    "nemotron_pii": BenchmarkSpec(
        benchmark_id="nemotron_pii",
        name="NVIDIA Nemotron-PII",
        source_url="https://huggingface.co/datasets/nvidia/Nemotron-PII",
        access="open",
        loader="jsonl_or_parquet_export",
        default_split="test",
        notes="Synthetic Hugging Face dataset with text and span labels. Export to JSONL locally before running.",
    ),
    "ai4privacy_300k": BenchmarkSpec(
        benchmark_id="ai4privacy_300k",
        name="AI4Privacy PII Masking 300k",
        source_url="https://huggingface.co/datasets/ai4privacy/pii-masking-300k",
        access="open_with_dataset_license",
        loader="jsonl_or_parquet_export",
        default_split="validation",
        notes="Synthetic/masked PII dataset with source_text and privacy_mask or span_labels fields.",
    ),
    "kaggle_pii": BenchmarkSpec(
        benchmark_id="kaggle_pii",
        name="Learning Agency Lab PII Data Detection",
        source_url="https://www.kaggle.com/competitions/pii-detection-removal-from-educational-data",
        access="account_or_terms",
        loader="kaggle_train_json",
        default_split="train",
        notes="Kaggle dataset uses token labels; requires user-managed download and terms acceptance.",
    ),
    "presidio_synthetic": BenchmarkSpec(
        benchmark_id="presidio_synthetic",
        name="Microsoft Presidio synthetic/evaluator format",
        source_url="https://microsoft.github.io/presidio/evaluation/",
        access="local_generated",
        loader="generic_span_jsonl",
        default_split="user_provided",
        notes="Use Presidio Research/generated samples exported to JSONL with text and spans/entities.",
    ),
    "n2c2_2014_deid": BenchmarkSpec(
        benchmark_id="n2c2_2014_deid",
        name="n2c2/i2b2 2014 De-identification",
        source_url="https://n2c2.dbmi.hms.harvard.edu/data-sets",
        access="access_controlled",
        loader="generic_span_jsonl_or_xml",
        default_split="user_provided",
        notes="Clinical de-identification benchmark; user must obtain data and provide a local converted file.",
    ),
}

ENTITY_MAP = {
    "account_number": "MRN",
    "address": "ADDRESS",
    "city": "ADDRESS",
    "country": "ADDRESS",
    "county": "ADDRESS",
    "date": "DATE",
    "date_of_birth": "DATE",
    "dob": "DATE",
    "email": "EMAIL",
    "first_name": "NAME",
    "givenname": "NAME",
    "i-name_student": "NAME",
    "last_name": "NAME",
    "location": "ADDRESS",
    "medical_record_number": "MRN",
    "mrn": "MRN",
    "name": "NAME",
    "name_student": "NAME",
    "patient": "NAME",
    "person": "NAME",
    "phone": "PHONE",
    "phone_number": "PHONE",
    "phone_num": "PHONE",
    "ssn": "SSN",
    "state": "ADDRESS",
    "street_address": "ADDRESS",
    "url": "URL",
    "url_personal": "URL",
}

INCLUDED_ENTITIES = {"ADDRESS", "DATE", "EMAIL", "MRN", "NAME", "NPI", "PHONE", "SSN", "URL"}


def list_benchmarks() -> list[dict[str, str]]:
    return [asdict(spec) for spec in BENCHMARK_SPECS.values()]


def load_benchmark_records(benchmark_id: str, input_path: str | Path, limit: int | None = None) -> list[BenchmarkRecord]:
    spec = _spec(benchmark_id)
    path = Path(input_path)
    if spec.loader == "kaggle_train_json":
        records = _load_kaggle_json(path, benchmark_id)
    elif path.suffix.lower() == ".xml":
        records = _load_simple_n2c2_xml(path, benchmark_id)
    else:
        records = _load_json_or_jsonl(path, benchmark_id)
    return records[:limit] if limit is not None else records


def convert_benchmark_to_eval(
    benchmark_id: str,
    input_path: str | Path,
    out_dir: str | Path,
    limit: int | None = None,
) -> Path:
    out = Path(out_dir)
    text_dir = out / "texts"
    text_dir.mkdir(parents=True, exist_ok=True)
    records = load_benchmark_records(benchmark_id, input_path, limit=limit)
    manifest_path = out / "benchmark_cases.jsonl"
    with manifest_path.open("w", encoding="utf-8") as handle:
        for record in records:
            safe_case_id = _safe_case_id(record.case_id)
            text_path = text_dir / f"{safe_case_id}.txt"
            text_path.write_text(record.text, encoding="utf-8")
            case = {
                "case_id": safe_case_id,
                "file": str(text_path),
                "expected_entities": record.expected_entities,
                "expected_min_risk_lane": "NEEDS_MANUAL_REVIEW" if record.expected_entities else "LIKELY_SAFE_AFTER_REVIEW",
                "benchmark_id": benchmark_id,
                "source_metadata": record.source_metadata,
            }
            handle.write(json.dumps(case, sort_keys=True) + "\n")
    return manifest_path


def run_benchmark(
    benchmark_id: str,
    input_path: str | Path,
    out_dir: str | Path,
    limit: int | None = None,
) -> dict[str, Any]:
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    spec = _spec(benchmark_id)
    manifest = convert_benchmark_to_eval(benchmark_id, input_path, out / "converted", limit=limit)
    results = run_eval(manifest, out / "eval")
    payload = {
        "benchmark_id": benchmark_id,
        "benchmark": asdict(spec),
        "converted_manifest": str(manifest),
        **{key: value for key, value in results.items() if key != "cases"},
        "cases": results["cases"],
    }
    (out / "benchmark_results.json").write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    shutil.copyfile(out / "eval" / "eval_report.md", out / "benchmark_report.md")
    return payload


def _spec(benchmark_id: str) -> BenchmarkSpec:
    try:
        return BENCHMARK_SPECS[benchmark_id]
    except KeyError as exc:
        known = ", ".join(sorted(BENCHMARK_SPECS))
        raise ValueError(f"unknown benchmark {benchmark_id!r}; known benchmarks: {known}") from exc


def _load_json_or_jsonl(path: Path, benchmark_id: str) -> list[BenchmarkRecord]:
    raw = path.read_text(encoding="utf-8")
    stripped = raw.lstrip()
    if stripped.startswith("["):
        rows = json.loads(raw)
    else:
        rows = [json.loads(line) for line in raw.splitlines() if line.strip()]
    return [_record_from_mapping(row, benchmark_id, index) for index, row in enumerate(rows)]


def _load_kaggle_json(path: Path, benchmark_id: str) -> list[BenchmarkRecord]:
    rows = json.loads(path.read_text(encoding="utf-8"))
    records: list[BenchmarkRecord] = []
    for index, row in enumerate(rows):
        labels = row.get("labels", [])
        tokens = row.get("tokens", [])
        text = row.get("full_text") or row.get("text") or " ".join(tokens)
        expected = sorted(
            {
                normalized
                for label in labels
                if label != "O"
                for normalized in [_normalize_entity(label)]
                if normalized
            }
        )
        case_id = str(row.get("document") or row.get("id") or f"{benchmark_id}_{index}")
        records.append(
            BenchmarkRecord(
                case_id=case_id,
                text=text,
                expected_entities=expected,
                source_metadata={"format": "kaggle_train_json", "benchmark_id": benchmark_id},
            )
        )
    return records


def _record_from_mapping(row: dict[str, Any], benchmark_id: str, index: int) -> BenchmarkRecord:
    text = row.get("text") or row.get("source_text") or row.get("full_text") or row.get("sentence")
    if not isinstance(text, str) or not text:
        raise ValueError(f"benchmark row {index} for {benchmark_id} has no text/source_text/full_text field")
    spans = _extract_spans(row)
    expected = sorted({entity for span in spans for entity in [_normalize_entity(_span_label(span))] if entity})
    case_id = str(row.get("uid") or row.get("id") or row.get("document") or f"{benchmark_id}_{index}")
    metadata = {
        "benchmark_id": benchmark_id,
        "source_id": case_id,
        "domain": str(row.get("domain", "")),
        "locale": str(row.get("locale", "")),
    }
    return BenchmarkRecord(case_id=case_id, text=text, expected_entities=expected, source_metadata=metadata)


def _extract_spans(row: dict[str, Any]) -> list[Any]:
    for key in ("spans", "privacy_mask", "entities", "annotations", "labels"):
        value = row.get(key)
        if isinstance(value, list):
            return value
    span_labels = row.get("span_labels")
    if isinstance(span_labels, str):
        try:
            parsed = json.loads(span_labels)
            if isinstance(parsed, list):
                return parsed
        except json.JSONDecodeError:
            return []
    return []


def _span_label(span: Any) -> str:
    if isinstance(span, dict):
        return str(span.get("label") or span.get("entity_type") or span.get("type") or span.get("category") or "")
    if isinstance(span, list | tuple) and len(span) >= 3:
        return str(span[2])
    return str(span)


def _normalize_entity(label: str) -> str | None:
    cleaned = label.strip()
    if not cleaned:
        return None
    cleaned = re.sub(r"^[BI]-", "", cleaned, flags=re.IGNORECASE)
    key = cleaned.lower().replace(" ", "_").replace("-", "_")
    mapped = ENTITY_MAP.get(key)
    if mapped:
        return mapped
    upper = key.upper()
    return upper if upper in INCLUDED_ENTITIES else None


def _safe_case_id(case_id: str) -> str:
    safe = re.sub(r"[^A-Za-z0-9_.-]+", "_", case_id).strip("._")
    return safe or "case"


def _load_simple_n2c2_xml(path: Path, benchmark_id: str) -> list[BenchmarkRecord]:
    raw = path.read_text(encoding="utf-8")
    text_match = re.search(r"<TEXT><!\[CDATA\[(.*?)\]\]></TEXT>", raw, flags=re.DOTALL)
    if not text_match:
        text_match = re.search(r"<TEXT>(.*?)</TEXT>", raw, flags=re.DOTALL)
    text = text_match.group(1).strip() if text_match else raw
    tag_labels = re.findall(r"<[^/!][^>]*\\bTYPE=[\"']([^\"']+)[\"'][^>]*/?>", raw, flags=re.IGNORECASE)
    expected = sorted({entity for label in tag_labels for entity in [_normalize_entity(label)] if entity})
    return [
        BenchmarkRecord(
            case_id=path.stem,
            text=text,
            expected_entities=expected,
            source_metadata={"format": "n2c2_xml", "benchmark_id": benchmark_id},
        )
    ]

