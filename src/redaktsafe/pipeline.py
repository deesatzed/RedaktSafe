from __future__ import annotations

from collections import Counter
from collections.abc import Callable
from uuid import uuid4

from redaktsafe.adapters import ADAPTER_FACTORIES, cached_adapter_factory
from redaktsafe.contracts import (
    ArtifactRef,
    DetectorMetadata,
    PacketRunResult,
    PipelineConfig,
    RedactionReport,
    Receipt,
    ResidualRiskAssessment,
    RiskLane,
    SafePacket,
    Severity,
    ValidationSummary,
    utc_now_iso,
    DetectedSpan,
)
from redaktsafe.adapters import load_optional_adapters
from redaktsafe.detectors import regex_detectors
from redaktsafe.detectors.span_merge import SEVERITY_RANK, merge_spans
from redaktsafe.services.dedup import deduplicate_exact_lines
from redaktsafe.services.profile import build_input_profile
from redaktsafe.services.redact import apply_redactions
from redaktsafe.util import sha256_text, stable_json_hash

REQUIRED_ARTIFACTS = [
    "redacted.txt",
    "safe_packet.json",
    "redaction_report.json",
    "receipt.json",
    "receipt.md",
    "validation_summary.json",
]

RESIDUAL_RISK_TEXT = "This output may retain residual re-identification risk. Review before downstream use."
NOT_COMPLIANCE_TEXT = "This tool is not a compliance guarantee and does not replace human review."


def run_packet_pipeline(
    raw_text: str,
    config: PipelineConfig | None = None,
    source_name: str | None = None,
    adapter_factories: dict[str, Callable[[dict], object]] | None = None,
) -> PacketRunResult:
    config = config or PipelineConfig()
    if len(raw_text) > config.max_input_chars:
        return _fail_closed(raw_text, config, source_name, "Input exceeds configured size limit.")

    try:
        deduped_text, dedup_summary = deduplicate_exact_lines(raw_text)
        detected = regex_detectors.detect(deduped_text) if config.deterministic_detectors_enabled else []
        optional_adapters = _load_configured_adapters(config, adapter_factories=adapter_factories)
        adapter_metadata = [adapter.metadata() for adapter in optional_adapters]
        detected.extend(_adapter_findings_to_spans(deduped_text, optional_adapters))
        spans = merge_spans(detected)
        redacted_text = apply_redactions(deduped_text, spans)
        counts = dict(sorted(Counter(span.entity_type for span in spans).items()))
        risk = _assess_risk(spans, dedup_summary)
        detector_ids = regex_detectors.detector_ids(spans)
        now = utc_now_iso()
        source_hash = sha256_text(raw_text)
        redacted_hash = sha256_text(redacted_text)
        packet_id = f"packet_{uuid4().hex[:16]}"
        receipt_id = f"receipt_{uuid4().hex[:16]}"
        profile = build_input_profile(
            raw_text,
            config,
            dedup_summary,
            len(spans),
            [span.severity for span in spans],
            source_name,
        )

        report = RedactionReport(
            detected_spans=spans,
            counts_by_entity_type=counts,
            detector_ids=detector_ids,
            risk_lane=risk.lane,
            warnings=_warnings_for_lane(risk.lane),
        )
        packet = SafePacket(
            packet_id=packet_id,
            created_at=now,
            source_hash=source_hash,
            redacted_text_hash=redacted_hash,
            redacted_text=redacted_text,
            sections=[{"title": "redacted_text", "text": redacted_text}],
            detected_entity_summary=counts,
            residual_risk=risk,
            limitations=[
                RESIDUAL_RISK_TEXT,
                NOT_COMPLIANCE_TEXT,
                "Deterministic detectors can miss context-dependent identifiers.",
            ],
            allowed_downstream_uses=[
                "Local review by an authorized user.",
                "Local downstream processing after manual review.",
            ],
            disallowed_downstream_uses=[
                "External sharing without separate approval and review.",
                "Patient-care recommendations or clinical decision-making.",
                "Use as proof that all identifiers were removed.",
            ],
            receipt_id=receipt_id,
        )
        receipt = Receipt(
            receipt_id=receipt_id,
            created_at=now,
            config_hash=stable_json_hash(config.model_dump(mode="json")),
            source_hash=source_hash,
            artifacts=[ArtifactRef(name=name, relative_path=name) for name in REQUIRED_ARTIFACTS],
            detectors_used=[DetectorMetadata(detector_id=detector_id) for detector_id in detector_ids],
            model_adapters_used=adapter_metadata,
            risk_lane=risk.lane,
            counts_by_entity_type=counts,
            dedup_summary=dedup_summary,
            policy_findings=_policy_findings(risk.lane),
            output_hashes={},
            warnings=_warnings_for_lane(risk.lane),
        )
        validation = ValidationSummary(
            artifact_completeness=True,
            required_artifacts=REQUIRED_ARTIFACTS,
            missing_artifacts=[],
            no_raw_input_in_receipt=True,
            risk_lane=risk.lane,
            strict_mode_would_fail=_strict_should_fail(risk.lane),
            warnings=_warnings_for_lane(risk.lane),
        )
        return PacketRunResult(
            redacted_text=redacted_text,
            safe_packet=packet,
            redaction_report=report,
            receipt=receipt,
            validation_summary=validation,
            input_profile=profile,
        )
    except Exception as exc:  # pragma: no cover - defensive fail-closed path
        return _fail_closed(raw_text, config, source_name, f"Pipeline error: {type(exc).__name__}")


def strict_should_fail(lane: RiskLane) -> bool:
    return _strict_should_fail(lane)


def _assess_risk(spans, dedup_summary: dict[str, int | float | bool]) -> ResidualRiskAssessment:
    if not spans:
        return ResidualRiskAssessment(
            lane=RiskLane.LIKELY_SAFE_AFTER_REVIEW,
            reasons=["No sensitive entities were detected by enabled deterministic detectors."],
            residual_risk_language=RESIDUAL_RISK_TEXT,
        )

    severities = [span.severity for span in spans]
    max_severity = max(severities, key=lambda item: SEVERITY_RANK[item])
    entity_types = {span.entity_type for span in spans}
    reasons: list[str] = []

    if Severity.CRITICAL in severities:
        reasons.append("Critical identifier pattern detected.")
    if "UNSAFE_EXPORT_INTENT" in entity_types:
        reasons.append("Unsafe downstream export intent detected.")
    if {"ADDRESS", "MRN", "PHONE", "DATE"}.issubset(entity_types):
        reasons.append("Multiple high-risk identifier classes detected together.")
    if bool(dedup_summary.get("possible_ehr_scaffold")):
        reasons.append("Duplicate-rich EHR-style scaffold detected.")

    if reasons or max_severity == Severity.CRITICAL:
        lane = RiskLane.NOT_LLM_SAFE
    else:
        lane = RiskLane.NEEDS_MANUAL_REVIEW
        reasons.append("Sensitive entities were detected and require manual review.")

    return ResidualRiskAssessment(
        lane=lane,
        reasons=reasons,
        residual_risk_language=RESIDUAL_RISK_TEXT,
    )


def _warnings_for_lane(lane: RiskLane) -> list[str]:
    warnings = [RESIDUAL_RISK_TEXT, NOT_COMPLIANCE_TEXT]
    if _strict_should_fail(lane):
        warnings.append("Strict mode treats this risk lane as fail-closed.")
    return warnings


def _policy_findings(lane: RiskLane) -> list[dict[str, str]]:
    return [
        {"policy": "residual_risk", "status": "review_required"},
        {"policy": "strict_mode", "status": "fail_closed" if _strict_should_fail(lane) else "allowed_after_review"},
    ]


def _strict_should_fail(lane: RiskLane) -> bool:
    return lane in {
        RiskLane.NEEDS_MANUAL_REVIEW,
        RiskLane.NOT_LLM_SAFE,
        RiskLane.PIPELINE_ERROR_FAIL_CLOSED,
    }


def _fail_closed(raw_text: str, config: PipelineConfig, source_name: str | None, reason: str) -> PacketRunResult:
    now = utc_now_iso()
    source_hash = sha256_text(raw_text)
    redacted_text = ""
    risk = ResidualRiskAssessment(
        lane=RiskLane.PIPELINE_ERROR_FAIL_CLOSED,
        reasons=[reason],
        residual_risk_language=RESIDUAL_RISK_TEXT,
    )
    profile = build_input_profile(
        raw_text,
        config,
        {"line_count": len(raw_text.splitlines()), "duplicate_line_count": 0, "duplicate_line_ratio": 0.0, "possible_ehr_scaffold": False},
        0,
        [],
        source_name,
    )
    report = RedactionReport(
        detected_spans=[],
        counts_by_entity_type={},
        detector_ids=[],
        risk_lane=risk.lane,
        warnings=[reason, RESIDUAL_RISK_TEXT, NOT_COMPLIANCE_TEXT],
    )
    receipt_id = f"receipt_{uuid4().hex[:16]}"
    packet = SafePacket(
        packet_id=f"packet_{uuid4().hex[:16]}",
        created_at=now,
        source_hash=source_hash,
        redacted_text_hash=sha256_text(redacted_text),
        redacted_text=redacted_text,
        sections=[],
        detected_entity_summary={},
        residual_risk=risk,
        limitations=[RESIDUAL_RISK_TEXT, NOT_COMPLIANCE_TEXT, reason],
        allowed_downstream_uses=["Local review of failure metadata."],
        disallowed_downstream_uses=["Downstream LLM use until the failure is resolved."],
        receipt_id=receipt_id,
    )
    receipt = Receipt(
        receipt_id=receipt_id,
        created_at=now,
        config_hash=stable_json_hash(config.model_dump(mode="json")),
        source_hash=source_hash,
        artifacts=[ArtifactRef(name=name, relative_path=name) for name in REQUIRED_ARTIFACTS],
        detectors_used=[],
        risk_lane=risk.lane,
        counts_by_entity_type={},
        dedup_summary=profile.model_dump(include={"line_count", "duplicate_line_count", "duplicate_line_ratio", "possible_ehr_scaffold"}),
        policy_findings=[{"policy": "pipeline", "status": "fail_closed", "reason": reason}],
        output_hashes={},
        warnings=[reason, RESIDUAL_RISK_TEXT, NOT_COMPLIANCE_TEXT],
    )
    validation = ValidationSummary(
        artifact_completeness=True,
        required_artifacts=REQUIRED_ARTIFACTS,
        missing_artifacts=[],
        no_raw_input_in_receipt=True,
        risk_lane=risk.lane,
        strict_mode_would_fail=True,
        warnings=[reason, RESIDUAL_RISK_TEXT, NOT_COMPLIANCE_TEXT],
    )
    return PacketRunResult(
        redacted_text=redacted_text,
        safe_packet=packet,
        redaction_report=report,
        receipt=receipt,
        validation_summary=validation,
        input_profile=profile,
    )


def _load_configured_adapters(config: PipelineConfig, adapter_factories: dict[str, Callable[[dict], object]] | None = None):
    factories = dict(ADAPTER_FACTORIES)
    if adapter_factories:
        factories.update(adapter_factories)
    adapters = []
    unknown_ids = []
    for adapter_id in config.adapters_enabled:
        settings = config.model_adapters.get(adapter_id, {})
        factory = factories.get(adapter_id)
        if factory:
            if adapter_factories and adapter_id in adapter_factories:
                adapters.append(factory(settings))
            else:
                adapters.append(cached_adapter_factory(adapter_id, settings))
        else:
            unknown_ids.append(adapter_id)
    if unknown_ids:
        adapters.extend(load_optional_adapters(unknown_ids))
    return adapters


def _adapter_findings_to_spans(text: str, adapters) -> list[DetectedSpan]:
    spans: list[DetectedSpan] = []
    for adapter in adapters:
        if not getattr(adapter, "available", False):
            continue
        for finding in adapter.detect(text):
            spans.append(
                DetectedSpan(
                    span_id=f"span_model_{sha256_text(f'{finding.adapter_id}:{finding.start}:{finding.end}:{finding.entity_type}')[:12]}",
                    start=finding.start,
                    end=finding.end,
                    entity_type=finding.entity_type,
                    replacement=f"[REDACTED_{finding.entity_type}]",
                    detectors=[finding.adapter_id],
                    confidence=finding.confidence,
                    severity=Severity(finding.severity),
                    text_hash=finding.text_hash or sha256_text(text[finding.start:finding.end]),
                )
            )
    return spans
