from redaktsafe.adapters import load_optional_adapters
from redaktsafe.adapters.fake_model_adapter import FakeModelAdapter
from redaktsafe.adapters.protocols import AdapterFinding
from redaktsafe.benchmark import benchmark_payload
from redaktsafe.pipeline import run_packet_pipeline


def test_optional_adapters_are_absent_by_default_without_breaking_pipeline():
    adapters = load_optional_adapters([])
    result = run_packet_pipeline("Patient Jane Doe, MRN E4567890.", source_name="adapter-test")

    assert adapters == []
    assert result.redaction_report.counts_by_entity_type["MRN"] == 1
    assert result.receipt.model_adapters_used == []


def test_stub_adapters_report_unavailable_metadata():
    adapters = load_optional_adapters(["openmed", "redaktorg", "agent_pidgin", "sentinel", "mlx"])

    assert [adapter.adapter_id for adapter in adapters] == ["openmed", "redaktorg", "agent_pidgin", "sentinel", "mlx"]
    assert all(adapter.available is False for adapter in adapters)
    assert all(adapter.metadata()["status"] == "unavailable" for adapter in adapters)


def test_adapter_finding_cannot_downgrade_deterministic_finding_shape():
    finding = AdapterFinding(
        adapter_id="fake",
        entity_type="NAME",
        start=0,
        end=4,
        confidence=0.4,
        severity="medium",
    )

    assert finding.entity_type == "NAME"
    assert finding.severity == "medium"


def test_fake_model_adapter_detects_without_external_model_download():
    adapter = FakeModelAdapter(entity_type="NAME", needle="Synthetic Person")

    findings = adapter.detect("Synthetic Person is present.")

    assert adapter.available is True
    assert findings[0].entity_type == "NAME"
    assert findings[0].adapter_id == "fake_model"
    assert adapter.metadata()["requires_download"] == "false"


def test_benchmark_payload_records_default_runtime_context():
    payload = benchmark_payload("eval", case_count=10, latency_ms=12.5)

    assert payload["benchmark_name"] == "eval"
    assert payload["case_count"] == 10
    assert payload["latency_ms"] == 12.5
    assert payload["network_required"] is False
    assert payload["model_download_required"] is False
