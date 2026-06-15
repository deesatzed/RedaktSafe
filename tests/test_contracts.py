import json

import pytest
from pydantic import ValidationError

from redaktsafe.contracts import Receipt, RiskLane


def test_receipt_forbids_raw_text_field():
    payload = _receipt_payload()
    payload["raw_text"] = "Patient Jane Doe"
    with pytest.raises(ValidationError):
        Receipt(**payload)


def test_receipt_requires_no_raw_input_flag_true():
    payload = _receipt_payload()
    payload["no_raw_input_copied"] = False
    with pytest.raises(ValidationError):
        Receipt(**payload)


def test_receipt_json_does_not_include_original_value():
    receipt = Receipt(**_receipt_payload())
    dumped = json.dumps(receipt.model_dump(mode="json"))
    assert "Jane Doe" not in dumped
    assert "raw_text" not in dumped


def _receipt_payload():
    return {
        "receipt_id": "receipt_test",
        "created_at": "2026-06-15T00:00:00+00:00",
        "config_hash": "abc",
        "source_hash": "def",
        "artifacts": [],
        "detectors_used": [],
        "risk_lane": RiskLane.NEEDS_MANUAL_REVIEW,
        "counts_by_entity_type": {},
        "dedup_summary": {},
        "policy_findings": [],
        "output_hashes": {},
        "warnings": [],
        "no_raw_input_copied": True,
    }

