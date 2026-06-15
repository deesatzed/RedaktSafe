import json
from pathlib import Path

from redaktsafe.cli import main
from redaktsafe.pipeline import REQUIRED_ARTIFACTS


def test_packet_command_writes_required_artifacts(tmp_path):
    out_dir = tmp_path / "packet"
    status = main(["packet", "fixtures/synthetic/simple_identifiers.txt", "--out", str(out_dir)])
    assert status == 0
    for name in REQUIRED_ARTIFACTS:
        assert (out_dir / name).exists(), name

    receipt = json.loads((out_dir / "receipt.json").read_text(encoding="utf-8"))
    receipt_blob = json.dumps(receipt)
    assert receipt["no_raw_input_copied"] is True
    assert "Jane Doe" not in receipt_blob
    assert "jane@example.com" not in receipt_blob


def test_strict_high_risk_packet_returns_nonzero(tmp_path):
    out_dir = tmp_path / "risk"
    status = main(["packet", "fixtures/synthetic/high_risk_mixed_identifiers.txt", "--out", str(out_dir), "--strict"])
    assert status == 3
    assert (out_dir / "receipt.json").exists()
    packet = json.loads((out_dir / "safe_packet.json").read_text(encoding="utf-8"))
    assert packet["residual_risk"]["lane"] == "NOT_LLM_SAFE"


def test_schemas_command_writes_schema_files(tmp_path):
    status = main(["schemas", "--out", str(tmp_path)])
    assert status == 0
    assert (Path(tmp_path) / "Receipt.schema.json").exists()

