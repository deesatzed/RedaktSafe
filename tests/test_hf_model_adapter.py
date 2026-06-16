from redaktsafe.adapters.hf_token_classifier_adapter import HuggingFaceTokenClassifierAdapter
from redaktsafe.contracts import PipelineConfig
from redaktsafe.pipeline import run_packet_pipeline


class FakeTokenPipeline:
    model = type("Model", (), {"config": type("Config", (), {"_name_or_path": "fake/pii-model"})()})()

    def __call__(self, text, aggregation_strategy=None):
        return [
            {
                "entity_group": "PERSON",
                "word": "Avery Stone",
                "start": text.index("Avery Stone"),
                "end": text.index("Avery Stone") + len("Avery Stone"),
                "score": 0.91,
            }
        ]


def test_hf_token_classifier_adapter_converts_model_entities_to_findings():
    adapter = HuggingFaceTokenClassifierAdapter(model_id="fake/pii-model", pipeline_factory=lambda _model_id, _token: FakeTokenPipeline())

    findings = adapter.detect("Consult completed for Avery Stone.")

    assert adapter.available is True
    assert findings[0].entity_type == "NAME"
    assert findings[0].start == 22
    assert findings[0].end == 33
    assert findings[0].confidence == 0.91
    assert adapter.metadata()["model_id"] == "fake/pii-model"


def test_pipeline_adds_hf_adapter_findings_without_dropping_deterministic_findings():
    config = PipelineConfig(
        adapters_enabled=["hf_token_classifier"],
        model_adapters={"hf_token_classifier": {"model_id": "fake/pii-model"}},
    )
    result = run_packet_pipeline(
        "Consult completed for Avery Stone. Email jane@example.com.",
        config=config,
        source_name="model-test",
        adapter_factories={"hf_token_classifier": lambda _settings: HuggingFaceTokenClassifierAdapter(model_id="fake/pii-model", pipeline_factory=lambda _model_id, _token: FakeTokenPipeline())},
    )

    counts = result.redaction_report.counts_by_entity_type
    assert counts["NAME"] == 1
    assert counts["EMAIL"] == 1
    assert "Avery Stone" not in result.redacted_text
    assert "jane@example.com" not in result.redacted_text
    assert result.receipt.model_adapters_used[0]["model_id"] == "fake/pii-model"


def test_run_eval_can_use_model_adapter_config(tmp_path):
    from redaktsafe.eval import run_eval

    fixture = tmp_path / "case.txt"
    fixture.write_text("Consult completed for Avery Stone.", encoding="utf-8")
    manifest = tmp_path / "cases.jsonl"
    manifest.write_text(
        '{"case_id":"model_name","file":"' + str(fixture) + '","expected_entities":["NAME"],"expected_min_risk_lane":"NEEDS_MANUAL_REVIEW"}\n',
        encoding="utf-8",
    )
    config = PipelineConfig(
        adapters_enabled=["hf_token_classifier"],
        model_adapters={"hf_token_classifier": {"model_id": "fake/pii-model"}},
    )

    result = run_eval(
        manifest,
        tmp_path / "out",
        config=config,
        adapter_factories={"hf_token_classifier": lambda _settings: HuggingFaceTokenClassifierAdapter(model_id="fake/pii-model", pipeline_factory=lambda _model_id, _token: FakeTokenPipeline())},
    )

    assert result["recall"] == 1.0
    assert result["precision"] == 1.0
