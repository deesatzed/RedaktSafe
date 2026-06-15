from __future__ import annotations


def deduplicate_exact_lines(text: str) -> tuple[str, dict[str, int | float | bool]]:
    lines = text.splitlines()
    seen: set[str] = set()
    output: list[str] = []
    duplicate_count = 0

    for line in lines:
        if line in seen:
            duplicate_count += 1
            continue
        seen.add(line)
        output.append(line)

    if text.endswith("\n") and output:
        deduped = "\n".join(output) + "\n"
    else:
        deduped = "\n".join(output)

    line_count = len(lines)
    duplicate_ratio = duplicate_count / line_count if line_count else 0.0
    possible_ehr_scaffold = duplicate_count > 0 and duplicate_ratio >= 0.25
    return deduped, {
        "line_count": line_count,
        "duplicate_line_count": duplicate_count,
        "duplicate_line_ratio": duplicate_ratio,
        "possible_ehr_scaffold": possible_ehr_scaffold,
    }

