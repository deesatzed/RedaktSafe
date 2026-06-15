from __future__ import annotations

import json
from pathlib import Path

from redaktsafe.contracts import ArtifactRef, PacketRunResult
from redaktsafe.pipeline import REQUIRED_ARTIFACTS
from redaktsafe.util import sha256_bytes


def write_artifacts(result: PacketRunResult, out_dir: Path) -> PacketRunResult:
    out_dir.mkdir(parents=True, exist_ok=True)

    payloads = {
        "redacted.txt": result.redacted_text,
        "safe_packet.json": _json(result.safe_packet.model_dump(mode="json")),
        "redaction_report.json": _json(result.redaction_report.model_dump(mode="json")),
        "receipt.md": _receipt_markdown(result),
        "validation_summary.json": _json(result.validation_summary.model_dump(mode="json")),
    }

    output_hashes: dict[str, str] = {}
    for name, payload in payloads.items():
        path = out_dir / name
        data = payload.encode("utf-8")
        path.write_bytes(data)
        output_hashes[name] = sha256_bytes(data)

    receipt = result.receipt.model_copy(
        update={
            "output_hashes": output_hashes,
            "artifacts": [
                ArtifactRef(name=name, relative_path=name, sha256=output_hashes.get(name))
                for name in REQUIRED_ARTIFACTS
            ],
        }
    )
    receipt_payload = _json(receipt.model_dump(mode="json"))
    receipt_path = out_dir / "receipt.json"
    receipt_data = receipt_payload.encode("utf-8")
    receipt_path.write_bytes(receipt_data)
    output_hashes["receipt.json"] = sha256_bytes(receipt_data)
    receipt = receipt.model_copy(update={"output_hashes": output_hashes})
    receipt_payload = _json(receipt.model_dump(mode="json"))
    receipt_path.write_text(receipt_payload, encoding="utf-8")

    return result.model_copy(update={"receipt": receipt})


def _json(value: object) -> str:
    return json.dumps(value, indent=2, sort_keys=True) + "\n"


def _receipt_markdown(result: PacketRunResult) -> str:
    receipt = result.receipt
    lines = [
        "# RedaktSafe Receipt",
        "",
        f"- Receipt ID: `{receipt.receipt_id}`",
        f"- Risk lane: `{receipt.risk_lane.value}`",
        f"- Source hash: `{receipt.source_hash}`",
        f"- No raw input copied: `{receipt.no_raw_input_copied}`",
        "",
        "This output may retain residual re-identification risk. Review before downstream use.",
        "This tool is not a compliance guarantee and does not replace human review.",
        "",
        "## Entity Counts",
    ]
    if receipt.counts_by_entity_type:
        for entity_type, count in sorted(receipt.counts_by_entity_type.items()):
            lines.append(f"- {entity_type}: {count}")
    else:
        lines.append("- No entities detected by enabled deterministic detectors.")
    lines.extend(["", "## Warnings"])
    for warning in receipt.warnings:
        lines.append(f"- {warning}")
    return "\n".join(lines) + "\n"

