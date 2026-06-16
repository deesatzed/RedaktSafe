# RedaktSafe Implementation Plan

## Goal

Build an end-to-end local application named `redaktsafe` that can install from a clean checkout, process synthetic or deidentified-style text locally, generate schema-backed artifacts and receipts, run evaluations, expose a local FastAPI service, and provide a minimal browser UI without cloud calls or compliance overclaims.

## Architecture

The app has four layers:

1. Input: local text file, pasted text, and synthetic fixtures.
2. Processing: input profile, exact-line deduplication, deterministic detection, optional adapter findings, span merge, redaction, sectioning, and residual-risk scoring.
3. Artifacts: `redacted.txt`, `safe_packet.json`, `redaction_report.json`, `receipt.json`, `receipt.md`, and `validation_summary.json`.
4. Interfaces: CLI first, local FastAPI second, minimal browser UI third, optional adapters last.

## Phase Order

### Phase 0: Repo and Package Bootstrap

- Initialize git only after documenting the handoff-folder state.
- Add `.gitignore`, `pyproject.toml`, package skeleton, tests, README, fixtures, and `doctor`.
- Verification: `python -m pytest`, `python -m redaktsafe.cli doctor`, and installed `redaktsafe doctor` when packaging is available.

### Phase 1: Contracts and Deterministic Baseline

- Add Pydantic contracts and schema export.
- Add deterministic regex detectors for email, phone, SSN-like IDs, MRN-like IDs, NPI-like IDs, dates, URLs, IP addresses, address-ish lines, and synthetic name patterns.
- Add exact-line deduplication, input profiling, span merge, and typed redaction.
- Verification: unit tests for contracts, schemas, detectors, dedup, merge, redaction, and no raw receipt fields.

### Phase 2: Packet Pipeline and CLI

- Implement `run_packet_pipeline`.
- Write all required artifacts.
- Add strict-mode fail-closed behavior.
- Verification: CLI packet runs for simple and high-risk fixtures, with no raw input or original spans in receipts.

### Phase 3: Evaluation Harness

- Add at least 10 synthetic regression fixtures and `evals/cases.jsonl`.
- Implement recall, precision, false positives, unsafe-pass count, latency, artifact completeness, receipt completeness, and no-raw-input checks.
- Verification: `python -m redaktsafe.cli eval --fixtures evals/cases.jsonl --out /tmp/redaktsafe-eval`.

### Phase 4: Local API

- Implement FastAPI endpoints: `/health`, `/api/preflight`, `/api/packet`, and `/api/artifacts/{run_id}/{artifact_name}`.
- Enforce input size limits and scoped artifact access.
- Verification: API tests cover healthy status, transient preflight, scoped packet writes, traversal blocking, symlink escape blocking, unrecognized artifact blocking, and input-size enforcement.

### Phase 5: Minimal Local UI

- Build a local UI for paste/upload, local preflight, risk lane, warnings, redacted review, entity summary, limitations, and artifact downloads.
- Use local API endpoints only. No analytics, telemetry, remote models, or compliance-overclaim copy.
- Verification: browser or automated smoke test proves a synthetic text can be processed and artifacts can be downloaded.

### Phase 6: Optional Adapter Interfaces

- Add interfaces or stubs for OpenMed, redaktorg, Agent Pidgin, Sentinel, and local model detectors only after baseline CLI, eval, API, and UI are working.
- Verification: tests prove the app works when adapters are absent and deterministic findings cannot be downgraded.

### Phase 7: Learning Audit, Gates, and Fine-Tuning Export

- Add opt-in encrypted learning correction storage and review queue.
- Add 24-hour-if-active audit behavior.
- Add context canaries for eponyms, patient surname context, institutions, buildings/units, and research labs.
- Add shadow-mode candidate mitigations with source correction IDs, severity score, gate results, promotion decision, version, and rollback reference.
- Add fine-tuning export/dry-run path that refuses readiness when reviewed correction volume is below the configured minimum.
- Verification: learning tests, canary command, audit command, fine-tuning dry-run, no-plaintext scans, and full test suite.

### Phase 8: Benchmark Recall, Reviewer UI, Teacher Adapter, and Taxonomy

- Add benchmark backend comparison for deterministic-only vs optional model-assisted runs.
- Add local reviewer UI and API endpoints for correction capture and review queue inspection.
- Add correction-corpus coverage summary.
- Add optional teacher-audit adapter injection and unavailable-model metadata.
- Expand taxonomy normalization/detection for IDs, usernames, institutions, labs, departments, buildings/units, provider names, and ambiguous eponyms.
- Verification: benchmark comparison tests, detector taxonomy tests, learning API/UI tests, teacher-adapter tests, full test suite, OpenMed sample comparison commands.

## First Implementation Batch

The first batch should complete Phase 0 and as much of Phases 1 and 2 as practical without skipping tests:

1. Create packaging, package skeleton, CLI entrypoint, README, `.gitignore`, and fixtures.
2. Write tests for `doctor`, schema export, detector basics, receipt raw-input exclusion, and CLI artifact creation.
3. Implement contracts, deterministic detectors, profile/dedup, span merge/redaction, packet pipeline, artifact writer, and strict mode.
4. Run the nearest verification commands and update `PROGRESS.md`.
