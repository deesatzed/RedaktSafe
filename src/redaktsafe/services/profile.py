from __future__ import annotations

from redaktsafe.contracts import InputProfile, PipelineConfig, Severity, utc_now_iso
from redaktsafe.detectors.span_merge import SEVERITY_RANK
from redaktsafe.util import stable_json_hash


def build_input_profile(
    raw_text: str,
    config: PipelineConfig,
    dedup_summary: dict[str, int | float | bool],
    detector_count: int,
    severities: list[Severity],
    source_name: str | None,
) -> InputProfile:
    max_severity = max(severities, key=lambda item: SEVERITY_RANK[item]) if severities else None
    return InputProfile(
        character_count=len(raw_text),
        line_count=int(dedup_summary["line_count"]),
        duplicate_line_count=int(dedup_summary["duplicate_line_count"]),
        duplicate_line_ratio=float(dedup_summary["duplicate_line_ratio"]),
        possible_ehr_scaffold=bool(dedup_summary["possible_ehr_scaffold"]),
        detector_count=detector_count,
        maximum_entity_severity=max_severity,
        config_hash=stable_json_hash(config.model_dump(mode="json")),
        source_name=source_name,
        created_at=utc_now_iso(),
    )

