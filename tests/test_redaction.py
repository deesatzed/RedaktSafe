from redaktsafe.detectors.regex_detectors import detect
from redaktsafe.detectors.span_merge import merge_spans
from redaktsafe.services.redact import apply_redactions


def test_redaction_uses_typed_tokens_without_original_values():
    text = "Patient Jane Doe, email jane@example.com."
    spans = merge_spans(detect(text))
    redacted = apply_redactions(text, spans)
    assert "[REDACTED_NAME]" in redacted
    assert "[REDACTED_EMAIL]" in redacted
    assert "Jane Doe" not in redacted
    assert "jane@example.com" not in redacted

