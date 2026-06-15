import json

from redaktsafe.pipeline import run_packet_pipeline


def test_pipeline_builds_packet_without_raw_receipt_values():
    raw = "Patient Jane Doe, MRN E4567890, phone 617-555-0142, email jane@example.com."
    result = run_packet_pipeline(raw, source_name="synthetic")
    receipt_json = json.dumps(result.receipt.model_dump(mode="json"))

    assert result.safe_packet.redacted_text
    assert result.safe_packet.receipt_id == result.receipt.receipt_id
    assert "Jane Doe" not in receipt_json
    assert "jane@example.com" not in receipt_json
    assert result.receipt.no_raw_input_copied is True


def test_high_risk_text_is_not_llm_safe():
    raw = """Name: Maria Rivera
MRN: MRN-992188
DOB: 04/05/1965
Phone: (212) 555-0101
Address: 123 Oak Street, Boston MA
Assessment: chest pain resolved.
"""
    result = run_packet_pipeline(raw, source_name="synthetic")
    assert result.safe_packet.residual_risk.lane.value == "NOT_LLM_SAFE"

