from __future__ import annotations

from redaktsafe.contracts import DetectedSpan


def apply_redactions(text: str, spans: list[DetectedSpan]) -> str:
    if not spans:
        return text

    chunks: list[str] = []
    cursor = 0
    for span in sorted(spans, key=lambda item: item.start):
        chunks.append(text[cursor:span.start])
        chunks.append(span.replacement)
        cursor = span.end
    chunks.append(text[cursor:])
    return "".join(chunks)

