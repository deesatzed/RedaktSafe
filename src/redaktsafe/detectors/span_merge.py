from __future__ import annotations

from redaktsafe.contracts import DetectedSpan, Severity
from redaktsafe.util import short_hash

SEVERITY_RANK = {
    Severity.LOW: 1,
    Severity.MEDIUM: 2,
    Severity.HIGH: 3,
    Severity.CRITICAL: 4,
}

ENTITY_PRIORITY = {
    "SSN": 100,
    "MRN": 90,
    "NPI": 85,
    "EMAIL": 80,
    "PHONE": 75,
    "ADDRESS": 70,
    "NAME": 60,
    "DATE": 50,
    "URL": 40,
    "IP_ADDRESS": 40,
}


def merge_spans(spans: list[DetectedSpan]) -> list[DetectedSpan]:
    if not spans:
        return []

    ordered = sorted(spans, key=lambda item: (item.start, item.end))
    merged: list[DetectedSpan] = []
    current = ordered[0]

    for candidate in ordered[1:]:
        if candidate.start <= current.end:
            current = _merge_pair(current, candidate)
        else:
            merged.append(current)
            current = candidate

    merged.append(current)
    return merged


def _merge_pair(left: DetectedSpan, right: DetectedSpan) -> DetectedSpan:
    chosen = _choose_entity(left, right)
    severity = max([left.severity, right.severity], key=lambda item: SEVERITY_RANK[item])
    confidence_values = [value for value in [left.confidence, right.confidence] if value is not None]
    confidence = max(confidence_values) if confidence_values else None
    start = min(left.start, right.start)
    end = max(left.end, right.end)
    detectors = sorted(set(left.detectors + right.detectors))
    text_hash = left.text_hash if left.start <= right.start else right.text_hash
    return DetectedSpan(
        span_id=f"span_{short_hash(f'{start}:{end}:{chosen}:{detectors}')}",
        start=start,
        end=end,
        entity_type=chosen,
        replacement=f"[REDACTED_{chosen}]",
        detectors=detectors,
        confidence=confidence,
        severity=severity,
        text_hash=text_hash,
    )


def _choose_entity(left: DetectedSpan, right: DetectedSpan) -> str:
    left_priority = ENTITY_PRIORITY.get(left.entity_type, 0)
    right_priority = ENTITY_PRIORITY.get(right.entity_type, 0)
    if left_priority == right_priority:
        return left.entity_type if (left.end - left.start) >= (right.end - right.start) else right.entity_type
    return left.entity_type if left_priority > right_priority else right.entity_type

