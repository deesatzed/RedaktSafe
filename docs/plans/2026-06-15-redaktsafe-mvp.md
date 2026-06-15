# RedaktSafe MVP Implementation Plan

> **For Codex:** REQUIRED SUB-SKILL: Use executing-plans to implement this plan task-by-task.

**Goal:** Build the RedaktSafe local CLI, artifact, evaluation, API, and UI MVP from the handoff package without network calls, credentials, real PHI, or compliance overclaims.

**Architecture:** The app uses a Python package with Pydantic contracts, deterministic detectors, a packet pipeline, CLI artifact writer, eval harness, FastAPI service, and a minimal local browser UI. Optional adapters remain isolated and cannot weaken deterministic findings.

**Tech Stack:** Python 3.12+, Pydantic v2, pytest, FastAPI, Uvicorn, standard-library CLI via argparse, and a minimal frontend served locally after the API is working.

---

## Task 1: Bootstrap Repository and Package

**Files:**

- Create: `.gitignore`
- Create: `pyproject.toml`
- Create: `README.md`
- Create: `src/redaktsafe/__init__.py`
- Create: `src/redaktsafe/cli.py`
- Create: `tests/test_cli_doctor.py`
- Create: `fixtures/synthetic/*.txt`

**Steps:**

1. Initialize git after `PROGRESS.md` records the initial non-repo state.
2. Add a `.gitignore` that excludes `.redaktsafe_runs/`, caches, virtualenvs, build artifacts, and OS noise.
3. Add package metadata and console script.
4. Add a minimal `doctor` command that reports local status without network checks.
5. Copy/adapt synthetic fixtures from the handoff into canonical `fixtures/synthetic/`.
6. Run `python -m pytest` and `python -m redaktsafe.cli doctor`.

## Task 2: Add Contracts and Schema Export

**Files:**

- Create: `src/redaktsafe/contracts.py`
- Modify: `src/redaktsafe/cli.py`
- Create: `tests/test_contracts.py`

**Steps:**

1. Write tests for required models and raw receipt field exclusion.
2. Implement Pydantic models for profiles, spans, reports, packets, risk, receipts, config, and run results.
3. Add `schemas --out DIR`.
4. Run targeted tests and schema export command.

## Task 3: Add Deterministic Detection, Dedup, Merge, and Redaction

**Files:**

- Create: `src/redaktsafe/detectors/regex_detectors.py`
- Create: `src/redaktsafe/detectors/span_merge.py`
- Create: `src/redaktsafe/services/profile.py`
- Create: `src/redaktsafe/services/dedup.py`
- Create: `src/redaktsafe/services/redact.py`
- Create: `tests/test_detectors.py`
- Create: `tests/test_redaction.py`

**Steps:**

1. Write detector tests for email, phone, SSN-like, MRN-like, NPI-like, dates, URLs, IPs, and synthetic names.
2. Write merge/redaction tests for overlapping spans and typed replacements.
3. Implement detectors and services.
4. Run targeted tests.

## Task 4: Add Pipeline, Artifact Writer, and Packet CLI

**Files:**

- Create: `src/redaktsafe/pipeline.py`
- Create: `src/redaktsafe/artifacts.py`
- Modify: `src/redaktsafe/cli.py`
- Create: `tests/test_pipeline_packet.py`
- Create: `tests/test_cli_packet.py`

**Steps:**

1. Write tests proving required artifacts are generated.
2. Write tests proving `receipt.json` omits raw input and original spans.
3. Implement pipeline and artifact writer.
4. Implement `packet`, `text`, and strict mode.
5. Run CLI proof commands for simple and high-risk fixtures.

## Task 5: Add Evaluation Harness

**Files:**

- Create: `evals/cases.jsonl`
- Create: `src/redaktsafe/eval.py`
- Modify: `src/redaktsafe/cli.py`
- Create: `tests/test_eval.py`

**Steps:**

1. Add 10 synthetic regression cases.
2. Implement recall, precision, false positives, unsafe-pass count, latency, artifact completeness, receipt completeness, and no-raw-input violations.
3. Write `eval_results.json` and `eval_report.md`.
4. Run eval proof command.

## Task 6: Add Local API

**Files:**

- Create: `src/redaktsafe/api/main.py`
- Create: `tests/test_api.py`

**Steps:**

1. Add `/health`, `/api/preflight`, `/api/packet`, and `/api/artifacts/{run_id}/{artifact_name}`.
2. Enforce input size limits and scoped artifact serving.
3. Test path traversal, absolute paths, symlink escapes, unknown artifacts, and oversize inputs.

## Task 7: Add Minimal Local UI

**Files:**

- Create: `frontend/`
- Create or modify docs for local UI command.

**Steps:**

1. Add paste/upload, local preflight, risk lane, redacted text, entity summary, limitations, and downloads.
2. Use local API only.
3. Run a browser or automated smoke test.

## Task 8: Add Optional Adapter Interfaces

**Files:**

- Create: `src/redaktsafe/adapters/`
- Create: `tests/test_adapters.py`

**Steps:**

1. Add deterministic-safe adapter protocols and absent-backend fallbacks.
2. Prove absent OpenMed, redaktorg, Agent Pidgin, Sentinel, MLX, and model backends do not break default operation.
3. Record adapter metadata in receipts only when enabled.

