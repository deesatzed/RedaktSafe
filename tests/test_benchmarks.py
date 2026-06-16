import json

from redaktsafe.benchmarks import (
    BENCHMARK_SPECS,
    convert_benchmark_to_eval,
    load_benchmark_records,
    run_benchmark,
)
from redaktsafe.cli import main


def test_benchmark_registry_includes_external_pii_benchmarks():
    expected = {
        "nemotron_pii",
        "ai4privacy_300k",
        "kaggle_pii",
        "presidio_synthetic",
        "n2c2_2014_deid",
    }

    assert expected.issubset(BENCHMARK_SPECS)
    assert BENCHMARK_SPECS["nemotron_pii"].access == "open"
    assert BENCHMARK_SPECS["kaggle_pii"].access == "account_or_terms"
    assert BENCHMARK_SPECS["n2c2_2014_deid"].access == "access_controlled"


def test_load_nemotron_pii_jsonl_records(tmp_path):
    source = tmp_path / "nemotron.jsonl"
    source.write_text(
        json.dumps(
            {
                "uid": "n1",
                "text": "I am Jason. My date of birth is 1987-05-22.",
                "spans": [
                    {"start": 5, "end": 10, "text": "Jason", "label": "first_name"},
                    {"start": 32, "end": 42, "text": "1987-05-22", "label": "date_of_birth"},
                ],
            }
        )
        + "\n",
        encoding="utf-8",
    )

    records = load_benchmark_records("nemotron_pii", source)

    assert records[0].case_id == "n1"
    assert records[0].text.startswith("I am Jason")
    assert records[0].expected_entities == ["DATE", "NAME"]


def test_load_ai4privacy_jsonl_records(tmp_path):
    source = tmp_path / "ai4privacy.jsonl"
    source.write_text(
        json.dumps(
            {
                "id": "a1",
                "source_text": "Email jane@example.com at 10:20am.",
                "privacy_mask": [
                    {"value": "jane@example.com", "start": 6, "end": 22, "label": "EMAIL"},
                    {"value": "10:20am", "start": 26, "end": 33, "label": "TIME"},
                ],
            }
        )
        + "\n",
        encoding="utf-8",
    )

    records = load_benchmark_records("ai4privacy_300k", source)

    assert records[0].case_id == "a1"
    assert records[0].expected_entities == ["EMAIL"]


def test_load_kaggle_json_records(tmp_path):
    source = tmp_path / "train.json"
    source.write_text(
        json.dumps(
            [
                {
                    "document": 7,
                    "tokens": ["My", "email", "is", "jane@example.com"],
                    "labels": ["O", "O", "O", "B-EMAIL"],
                }
            ]
        ),
        encoding="utf-8",
    )

    records = load_benchmark_records("kaggle_pii", source)

    assert records[0].case_id == "7"
    assert records[0].text == "My email is jane@example.com"
    assert records[0].expected_entities == ["EMAIL"]


def test_convert_benchmark_to_eval_writes_cases_and_text_files(tmp_path):
    source = tmp_path / "presidio.jsonl"
    source.write_text(
        json.dumps(
            {
                "id": "p1",
                "text": "Call 617-555-0142.",
                "spans": [{"start": 5, "end": 17, "entity_type": "PHONE_NUMBER"}],
            }
        )
        + "\n",
        encoding="utf-8",
    )

    manifest = convert_benchmark_to_eval("presidio_synthetic", source, tmp_path / "converted")
    case = json.loads(manifest.read_text(encoding="utf-8").splitlines()[0])

    assert case["case_id"] == "p1"
    assert case["expected_entities"] == ["PHONE"]
    assert (tmp_path / "converted" / "texts" / "p1.txt").exists()


def test_run_benchmark_reuses_eval_metrics(tmp_path):
    source = tmp_path / "presidio.jsonl"
    source.write_text(
        json.dumps(
            {
                "id": "p1",
                "text": "Call 617-555-0142.",
                "spans": [{"start": 5, "end": 17, "entity_type": "PHONE_NUMBER"}],
            }
        )
        + "\n",
        encoding="utf-8",
    )

    result = run_benchmark("presidio_synthetic", source, tmp_path / "bench")

    assert result["benchmark_id"] == "presidio_synthetic"
    assert result["case_count"] == 1
    assert result["unsafe_pass_count"] == 0
    assert (tmp_path / "bench" / "benchmark_results.json").exists()


def test_benchmark_cli_lists_and_runs_local_sample(tmp_path, capsys):
    source = tmp_path / "presidio.jsonl"
    source.write_text(
        json.dumps(
            {
                "id": "p1",
                "text": "Call 617-555-0142.",
                "spans": [{"start": 5, "end": 17, "entity_type": "PHONE_NUMBER"}],
            }
        )
        + "\n",
        encoding="utf-8",
    )

    assert main(["benchmark", "list"]) == 0
    assert "nemotron_pii" in capsys.readouterr().out
    assert main(["benchmark", "run", "--source", "presidio_synthetic", "--input", str(source), "--out", str(tmp_path / "out")]) == 0
    assert (tmp_path / "out" / "benchmark_results.json").exists()

