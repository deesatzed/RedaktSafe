from __future__ import annotations

import re
from collections.abc import Iterable

from redaktsafe.contracts import DetectedSpan, Severity
from redaktsafe.util import sha256_text, short_hash


DETECTOR_VERSION = "0.1.0"


PATTERNS: list[tuple[str, str, str, Severity, float]] = [
    ("UNSAFE_EXPORT_INTENT", r"\b(?:upload|send|share|export)\b.{0,40}\b(?:cloud|chatbot|external|internet|LLM)\b", "regex_unsafe_export_intent", Severity.CRITICAL, 0.9),
    ("EMAIL", r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b", "regex_email", Severity.HIGH, 1.0),
    ("PHONE", r"(?<!\d)(?:\+?1[\s.-]?)?(?:\(\d{3}\)|\d{3})[\s.-]\d{3}[\s.-]\d{4}(?!\d)", "regex_phone", Severity.HIGH, 1.0),
    ("SSN", r"\b\d{3}-\d{2}-\d{4}\b", "regex_ssn", Severity.CRITICAL, 1.0),
    ("MRN", r"\b(?:MRN[:\s-]*)?[A-Z]\d{7,9}\b|\bMRN[-:\s]*\d{5,12}\b", "regex_mrn", Severity.HIGH, 1.0),
    ("NPI", r"\bNPI[:\s-]*\d{10}\b", "regex_npi", Severity.HIGH, 1.0),
    ("DATE", r"\b(?:DOB[:\s]*)?(?:\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|\d{4}-\d{2}-\d{2})\b", "regex_date", Severity.MEDIUM, 0.95),
    ("URL", r"\bhttps?://[^\s)]+", "regex_url", Severity.MEDIUM, 1.0),
    ("IP_ADDRESS", r"\b(?:\d{1,3}\.){3}\d{1,3}\b", "regex_ip_address", Severity.MEDIUM, 0.9),
    ("ADDRESS", r"\b\d{1,6}\s+[A-Z][A-Za-z0-9.'-]*(?:\s+[A-Z][A-Za-z0-9.'-]*){0,5}\s+(?:Street|St|Avenue|Ave|Road|Rd|Drive|Dr|Lane|Ln|Boulevard|Blvd)\b(?:,\s*[A-Z][A-Za-z .-]+)?", "regex_address", Severity.HIGH, 0.9),
]

NAME_TOKEN = r"(?:[A-Z][a-z]+|[A-Z])"
NAME_VALUE = rf"{NAME_TOKEN}(?:\s+{NAME_TOKEN}){{1,2}}"

NAME_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    (re.compile(rf"\bName:\s*({NAME_VALUE})\b"), "regex_name_label"),
    (re.compile(rf"\bN\s*a\s*m\s*e:\s*({NAME_VALUE})\b"), "regex_ocr_name_label"),
    (re.compile(rf"\bPatient\s+({NAME_VALUE})(?=\s+(?:reports|presented|states|can|with)|,|\n|$)"), "regex_patient_name"),
    (re.compile(rf"\bparticipant\s+({NAME_VALUE})(?=,|\.|\n|$)"), "regex_participant_name"),
]


def detect(text: str) -> list[DetectedSpan]:
    spans: list[DetectedSpan] = []
    for entity_type, pattern, detector_id, severity, confidence in PATTERNS:
        for match in re.finditer(pattern, text):
            spans.append(_span(text, match.start(), match.end(), entity_type, detector_id, severity, confidence))

    for pattern, detector_id in NAME_PATTERNS:
        for match in pattern.finditer(text):
            start, end = match.span(1)
            spans.append(_span(text, start, end, "NAME", detector_id, Severity.HIGH, 0.9))

    return sorted(spans, key=lambda item: (item.start, item.end, item.entity_type))


def detector_ids(spans: Iterable[DetectedSpan]) -> list[str]:
    ids: set[str] = set()
    for span in spans:
        ids.update(span.detectors)
    return sorted(ids)


def _span(
    text: str,
    start: int,
    end: int,
    entity_type: str,
    detector_id: str,
    severity: Severity,
    confidence: float,
) -> DetectedSpan:
    original = text[start:end]
    replacement = f"[REDACTED_{entity_type}]"
    return DetectedSpan(
        span_id=f"span_{short_hash(f'{start}:{end}:{entity_type}:{original}')}",
        start=start,
        end=end,
        entity_type=entity_type,
        replacement=replacement,
        detectors=[detector_id],
        confidence=confidence,
        severity=severity,
        text_hash=sha256_text(original),
    )
