# 02 — Architecture and Data Flow

## System overview

RedaktSafe is a local-first preflight workbench. It has four layers:

1. **Input layer** — accepts text files or pasted text.
2. **Processing layer** — profiles, deduplicates, redacts, sections, normalizes, and scores risk.
3. **Artifact layer** — writes safe packet, redaction report, receipt, and optional reviewer HTML/Markdown.
4. **Interface layer** — CLI first, local web UI second, SDK third.

## High-level flow

```text
raw input
  -> input profile
  -> exact-line dedup
  -> deterministic structured-ID detection
  -> optional token classifier / PHI model adapter
  -> redaction merge + conflict resolution
  -> conservative cleanup / section normalization
  -> residual-risk scoring
  -> safe packet generation
  -> receipt generation
  -> human review/export
```

## Why this order matters

Do not aggressively trim before redaction. The product should preserve the safety insight from redaktorg: cleanup that removes raw lines before PHI detection can hide sensitive identifiers from the detector. Therefore:

```text
safe default = dedup -> redact -> conservative reorganize
```

Aggressive trim, if ever implemented, must be opt-in, post-redaction, and blocked from dropping lines containing redaction tags or protected section anchors.

## Proposed repository structure

```text
redaktsafe-packet-workbench/
  pyproject.toml
  README.md
  CODEX.md
  src/redaktsafe/
    __init__.py
    cli.py
    config.py
    contracts.py
    pipeline.py
    detectors/
      __init__.py
      regex_detectors.py
      lexicon_detector.py
      model_detector.py
      span_merge.py
    services/
      profile.py
      dedup.py
      redact.py
      section.py
      risk.py
      packet.py
      receipt.py
      validation.py
    adapters/
      redaktorg_adapter.py
      agent_pidgin_adapter.py
      sentinel_adapter.py
      mlx_model_adapter.py
    api/
      main.py
      routes.py
      schemas.py
    ui_static/               # optional built frontend output
  frontend/
    package.json
    src/
      App.tsx
      api.ts
      components/
        InputPanel.tsx
        RedactionReview.tsx
        PacketSummary.tsx
        ReceiptPanel.tsx
        RiskBadge.tsx
  fixtures/
    synthetic/
      simple_identifiers.txt
      ehr_duplicate_scaffold.txt
      clinical_false_positive.txt
      high_risk_mixed_identifiers.txt
  tests/
    test_regex_detectors.py
    test_dedup.py
    test_redaction_merge.py
    test_pipeline_packet.py
    test_receipt_schema.py
    test_no_raw_input_in_receipts.py
    test_cli.py
    test_api.py
  evals/
    run_eval.py
    expected_findings.jsonl
  docs/
    SECURITY.md
    MODEL_ADAPTERS.md
    USER_GUIDE.md
```

## Core contracts

Use Pydantic models for:

- `InputProfile`
- `DetectedSpan`
- `RedactionReport`
- `SafePacket`
- `ResidualRiskAssessment`
- `Receipt`
- `PipelineConfig`
- `EvalCase`
- `EvalResult`

Keep schemas exported in `schemas/`.

## Deterministic detectors

Implement deterministic baseline before model adapters:

- email addresses;
- phone numbers;
- SSN-like patterns;
- MRN-like patterns configurable by regex;
- dates and DOB-like contexts;
- URL and IP-like patterns;
- NPI-like patterns;
- address-ish lines;
- bracketed names in fixtures;
- obvious name patterns only in synthetic fixtures unless a model/lexicon is enabled.

## Model adapters

Model adapters are optional plugins:

- token classifier for PII/PHI spans;
- clinical section classifier;
- residual-risk classifier;
- packet normalizer.

Model adapter interface:

```python
class SpanDetector(Protocol):
    detector_id: str
    version: str
    def detect(self, text: str, profile: InputProfile) -> list[DetectedSpan]: ...
```

All model outputs must be merged with deterministic detectors. Model adapters cannot downgrade deterministic findings.

## Risk lanes

Use explicit lanes:

- `SAFE_FOR_LOCAL_REVIEW`
- `LIKELY_SAFE_AFTER_REVIEW`
- `NEEDS_MANUAL_REVIEW`
- `NOT_LLM_SAFE`
- `PIPELINE_ERROR_FAIL_CLOSED`

Never label output as universally safe. Say what it is safe for: local review, downstream local LLM, or external sharing only after separate approval.

## Artifact policy

The output directory should contain:

```text
out/
  redacted.txt
  safe_packet.json
  redaction_report.json
  receipt.json
  receipt.md
  review.html          # optional
  validation_summary.json
```

`receipt.json` must not contain raw text. It may contain hashes, detector summaries, counts, config, and artifact paths.

## API endpoints

Minimum FastAPI endpoints:

- `GET /health`
- `POST /api/preflight` — returns transient report from text.
- `POST /api/packet` — creates packet artifacts in local workspace.
- `GET /api/artifacts/{run_id}/{name}` — returns generated artifacts only.

Do not expose arbitrary file reads.

## CLI commands

Minimum:

```bash
redaktsafe packet input.txt --out outdir
redaktsafe text "Patient Jane Doe..." --out outdir
redaktsafe eval --fixtures fixtures/synthetic
redaktsafe schemas --out schemas
redaktsafe doctor
```

## Expansion architecture

After MVP:

- Sentinel adapter converts `SafePacket` into governance episode draft.
- Agent Pidgin adapter emits semantic contract receipts.
- loclM3 adapter can use safe packets as local-model context.
- Honest Broker adapter parses safe packet into research intake draft.
- Agent Guard can use RedaktSafe as preflight for any text/file an agent attempts to transmit.
