# Codex Phase 0–2 Prompt

Build the deterministic CLI MVP for RedaktSafe.

Scope:

- Python package.
- Pydantic contracts.
- Deterministic detectors.
- Exact-line dedup.
- Span merge.
- Redaction.
- Residual risk lane.
- Safe packet.
- Receipt JSON and Markdown.
- CLI commands.
- Synthetic fixtures.
- Tests.

Do not build frontend yet.
Do not add real model downloads yet.
Do not depend on external APIs.

Commands that must pass:

```bash
python -m pytest
redaktsafe doctor
redaktsafe packet fixtures/synthetic/simple_identifiers.txt --out /tmp/redaktsafe-simple
redaktsafe packet fixtures/synthetic/high_risk_mixed_identifiers.txt --out /tmp/redaktsafe-risk --strict
```

Artifacts required:

- redacted.txt
- safe_packet.json
- redaction_report.json
- receipt.json
- receipt.md
- validation_summary.json

Tests required:

- no raw input in receipt;
- structured identifiers detected;
- duplicate lines profiled;
- strict mode fails closed;
- overlapping spans merge deterministically.
