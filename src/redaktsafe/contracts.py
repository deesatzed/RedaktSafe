from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator

SCHEMA_VERSION = "0.1.0"
PIPELINE_VERSION = "redaktsafe-deterministic-0.1.0"


class RiskLane(str, Enum):
    SAFE_FOR_LOCAL_REVIEW = "SAFE_FOR_LOCAL_REVIEW"
    LIKELY_SAFE_AFTER_REVIEW = "LIKELY_SAFE_AFTER_REVIEW"
    NEEDS_MANUAL_REVIEW = "NEEDS_MANUAL_REVIEW"
    NOT_LLM_SAFE = "NOT_LLM_SAFE"
    PIPELINE_ERROR_FAIL_CLOSED = "PIPELINE_ERROR_FAIL_CLOSED"


class Severity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class PipelineConfig(StrictModel):
    max_input_chars: int = 200_000
    fail_closed_on_uncertainty: bool = True
    deterministic_detectors_enabled: bool = True
    adapters_enabled: list[str] = Field(default_factory=list)
    model_adapters: dict[str, dict[str, str | float | int | bool]] = Field(default_factory=dict)


class InputProfile(StrictModel):
    character_count: int
    line_count: int
    duplicate_line_count: int
    duplicate_line_ratio: float
    possible_ehr_scaffold: bool
    detector_count: int = 0
    maximum_entity_severity: Severity | None = None
    config_hash: str
    source_name: str | None = None
    created_at: str


class DetectedSpan(StrictModel):
    span_id: str
    start: int = Field(ge=0)
    end: int = Field(ge=0)
    entity_type: str
    replacement: str
    detectors: list[str]
    confidence: float | None = Field(default=None, ge=0, le=1)
    severity: Severity
    text_hash: str

    @field_validator("end")
    @classmethod
    def end_must_be_after_start(cls, value: int, info: Any) -> int:
        start = info.data.get("start")
        if start is not None and value <= start:
            raise ValueError("end must be greater than start")
        return value


class RedactionReport(StrictModel):
    schema_version: str = SCHEMA_VERSION
    detected_spans: list[DetectedSpan]
    counts_by_entity_type: dict[str, int]
    detector_ids: list[str]
    risk_lane: RiskLane
    warnings: list[str]


class ResidualRiskAssessment(StrictModel):
    lane: RiskLane
    reasons: list[str]
    review_required: bool = True
    residual_risk_language: str


class SafePacket(StrictModel):
    packet_id: str
    schema_version: str = SCHEMA_VERSION
    created_at: str
    source_hash: str
    redacted_text_hash: str
    redacted_text: str
    sections: list[dict[str, str]]
    detected_entity_summary: dict[str, int]
    residual_risk: ResidualRiskAssessment
    limitations: list[str]
    allowed_downstream_uses: list[str]
    disallowed_downstream_uses: list[str]
    receipt_id: str


class ArtifactRef(StrictModel):
    name: str
    sha256: str | None = None
    relative_path: str


class DetectorMetadata(StrictModel):
    detector_id: str
    version: str = "0.1.0"
    kind: str = "deterministic"


class Receipt(StrictModel):
    receipt_id: str
    schema_version: str = SCHEMA_VERSION
    created_at: str
    pipeline_version: str = PIPELINE_VERSION
    config_hash: str
    source_hash: str
    artifacts: list[ArtifactRef]
    detectors_used: list[DetectorMetadata]
    model_adapters_used: list[dict[str, str]] = Field(default_factory=list)
    risk_lane: RiskLane
    counts_by_entity_type: dict[str, int]
    dedup_summary: dict[str, int | float | bool]
    policy_findings: list[dict[str, str]]
    output_hashes: dict[str, str]
    warnings: list[str]
    no_raw_input_copied: bool = True

    @field_validator("no_raw_input_copied")
    @classmethod
    def raw_input_flag_must_be_true(cls, value: bool) -> bool:
        if value is not True:
            raise ValueError("receipts must not copy raw input")
        return value


class ValidationSummary(StrictModel):
    schema_version: str = SCHEMA_VERSION
    artifact_completeness: bool
    required_artifacts: list[str]
    missing_artifacts: list[str]
    no_raw_input_in_receipt: bool
    risk_lane: RiskLane
    strict_mode_would_fail: bool
    warnings: list[str]


class PacketRunResult(StrictModel):
    redacted_text: str
    safe_packet: SafePacket
    redaction_report: RedactionReport
    receipt: Receipt
    validation_summary: ValidationSummary
    input_profile: InputProfile


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def schema_models() -> dict[str, type[BaseModel]]:
    return {
        "DetectedSpan": DetectedSpan,
        "InputProfile": InputProfile,
        "Receipt": Receipt,
        "RedactionReport": RedactionReport,
        "ResidualRiskAssessment": ResidualRiskAssessment,
        "SafePacket": SafePacket,
        "ValidationSummary": ValidationSummary,
    }
