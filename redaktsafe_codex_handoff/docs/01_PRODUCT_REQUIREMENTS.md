# 01 — Product Requirements Document

## Product name

RedaktSafe Trust Packet Workbench

## Primary job-to-be-done

When I have a messy clinical, research, or governance text artifact, I want to safely prepare it for downstream AI or human review so that I can reduce privacy risk, preserve useful context, and prove what happened.

## Initial users

Primary:

- clinician-informaticists;
- clinical researchers;
- health data analysts;
- AI governance reviewers;
- QI/safety teams;
- healthcare software developers.

Secondary:

- coding-agent users working with sensitive test data;
- honest-broker/data-request teams;
- local LLM builders;
- clinical app prototypers.

## Pain points

Current workflows often include:

- manual redaction that is slow and error-prone;
- regex-only redaction that misses context-dependent identifiers;
- cloud AI use before safety checks;
- messy EHR exports with duplicated scaffolding;
- no proof of what was removed or retained;
- no residual-risk scoring;
- no standard packet format for downstream tools.

## MVP user stories

### US-001: Create safe packet from a text file

As a user, I can run:

```bash
redaktsafe packet note.txt --out ./out
```

and receive a redacted text file, structured JSON packet, redaction report, and receipt.

Acceptance:

- command runs locally without network access;
- raw input is not copied into receipt;
- all artifacts are written to the output directory;
- summary states residual risk and limitations.

### US-002: Paste text into local UI

As a user, I can paste text into a browser UI served at `127.0.0.1`, click Preflight, and review redacted output before export.

Acceptance:

- UI works without external services;
- user can inspect redaction spans;
- user can download safe packet and receipt;
- browser never sends input to any remote endpoint.

### US-003: Review redaction report

As a user, I can see which entities were detected, which deterministic rules fired, and which spans were preserved as clinical anchors.

Acceptance:

- report includes entity type, start/end offsets for redacted text, detector source, confidence if available, and replacement token;
- report includes duplicate-line profile and cleanup actions;
- report includes residual-risk lane.

### US-004: Fail closed on unsafe uncertainty

As a user, I am warned when residual PII risk is above threshold or the tool cannot confidently classify safety.

Acceptance:

- unsafe or uncertain output is marked `NOT_LLM_SAFE`;
- CLI exits with nonzero code when `--strict` is set and risk is high;
- UI disables “export as safe” until user acknowledges residual risk.

### US-005: Emit reconstructable receipt

As a user, I can prove the path used to create a packet.

Acceptance:

- receipt includes input hash, pipeline version, detectors used, model identifiers if any, config hash, output hash, timestamp, and residual-risk lane;
- receipt excludes raw input text;
- receipt has stable schema and tests.

## Non-goals for MVP

- Do not provide clinical advice.
- Do not claim legal compliance.
- Do not ingest live EHR data.
- Do not support cloud model calls by default.
- Do not fine-tune models inside the MVP unless deterministic baseline is complete.
- Do not build a broad patient-facing assistant.

## Functional requirements

1. Input support: `.txt`, pasted text, optional `.md`.
2. Deterministic detectors: email, phone, SSN, MRN-like IDs, NPI-like IDs, dates, URLs, postal-ish addresses, names via configurable lexicon/demo model when available.
3. Dedup: exact-line deduplication before model inference while preserving at least one copy of each unique line.
4. Redaction: replacement tokens must preserve type, e.g. `[REDACTED_DATE]`.
5. Cleanup: conservative reorganization only after redaction.
6. Safe packet schema: structured sections, redacted text, metadata, risk assessment, receipt pointer.
7. Receipt: JSON and Markdown.
8. Evaluation harness: synthetic fixture tests with expected findings.
9. Config: local YAML/TOML config with no secrets required.
10. Audit: all generated artifacts must be traceable by hash.

## Nonfunctional requirements

- Local by default.
- Works without GPU; MLX acceleration optional on Apple Silicon.
- Reasonable latency for interactive use.
- Deterministic baseline must pass before model adapters are enabled.
- Test suite must run in clean clone without external credentials.
- Code must be typed and schema-backed.

## Product success metrics

- User can create first packet in under 5 minutes after clone/install.
- Time to prepare a messy document is reduced by at least 50% in user testing.
- Zero known unsafe-pass on bundled high-risk fixtures.
- Receipt schema validates for every run.
- Users understand limitations after reading generated report.
