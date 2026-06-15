# 04 — Build Plan and Milestones

## Build sequence

Codex should build in phases. Do not skip deterministic foundations for UI polish or model experimentation.

## Phase 0 — Repo bootstrap

Goal: clean local project that runs tests.

Tasks:

- create Python package structure;
- add `pyproject.toml`;
- add baseline README and safety language;
- configure pytest;
- add `.gitignore` for runs/artifacts;
- add initial schemas directory;
- add synthetic fixtures.

Definition of done:

- `python -m pytest` passes;
- `redaktsafe doctor` runs;
- no network dependency required.

## Phase 1 — Contracts and deterministic detectors

Goal: schema-backed pipeline primitives.

Tasks:

- implement Pydantic contracts;
- implement regex detectors;
- implement span merge;
- implement redaction replacement;
- implement input profiling;
- implement exact-line dedup;
- implement receipt skeleton.

Definition of done:

- unit tests cover every detector;
- span overlaps behave deterministically;
- receipts do not contain raw input.

## Phase 2 — Packet pipeline and CLI

Goal: one command creates usable artifacts.

Tasks:

- implement `run_packet_pipeline`;
- implement artifact writer;
- implement Markdown receipt;
- implement CLI commands;
- add fixtures and expected outputs;
- add strict mode.

Definition of done:

```bash
redaktsafe packet fixtures/synthetic/high_risk_mixed_identifiers.txt --out /tmp/redaktsafe-demo --strict
```

produces redacted text, safe packet, report, receipt, and validation summary.

## Phase 3 — Evaluation harness

Goal: measurable accuracy and safety.

Tasks:

- create JSONL eval cases;
- implement `redaktsafe eval`;
- compute recall/precision by entity type;
- compute unsafe-pass count;
- fail CI if unsafe-pass fixtures pass incorrectly;
- generate eval report Markdown.

Definition of done:

- eval suite runs without external data;
- unsafe-pass count is zero on bundled high-risk suite;
- metrics are printed and saved.

## Phase 4 — Local API

Goal: programmatic and UI-ready service.

Tasks:

- implement FastAPI app;
- add `/health`, `/api/preflight`, `/api/packet`, `/api/artifacts/{run_id}/{name}`;
- add path traversal tests;
- add input size limits;
- add no-raw-logs tests.

Definition of done:

- API tests pass;
- artifacts route only serves generated artifacts;
- no arbitrary local file read possible.

## Phase 5 — Minimal UI

Goal: user can paste text and download outputs.

Tasks:

- create Vite React app;
- implement input panel;
- implement risk summary;
- implement redacted output viewer;
- implement entity table;
- implement download links;
- add smoke tests if feasible.

Definition of done:

- user can run local server and create packet from pasted synthetic text;
- UI states limitations and local-only status;
- no external analytics or remote endpoints.

## Phase 6 — Adapter layer

Goal: plug in existing repos without hard dependency failure.

Tasks:

- implement `redaktorg_adapter` with graceful fallback;
- implement `agent_pidgin_adapter` contract stub;
- implement `sentinel_adapter` export stub;
- write docs for enabling adapters.

Definition of done:

- app works when adapters are absent;
- tests verify graceful degradation;
- adapter metadata appears in receipt when enabled.

## Phase 7 — Small-model adapters

Goal: accuracy-for-size experiments.

Tasks:

- define model adapter interface;
- implement local model config;
- support MLX model path or Hugging Face id if user explicitly enables;
- implement PHI/token classifier adapter stub;
- implement residual-risk classifier adapter stub;
- add benchmark script.

Definition of done:

- deterministic baseline remains default;
- model adapter tests can run with a fake model;
- real model evaluation is opt-in and skipped in CI unless enabled.

## Phase 8 — Sentinel and Agent Guard expansion tracks

Goal: use RedaktSafe as shared trust input layer.

Tasks:

- export safe packet to Sentinel episode draft shape;
- export Agent Pidgin-style receipt envelope;
- define CLI bridge commands;
- document future integration path.

Definition of done:

- no raw text leaves RedaktSafe boundary;
- bridge artifacts are schema-valid;
- limitations remain explicit.

## Release gate for MVP v0.1

MVP v0.1 can ship when:

- CLI works;
- API works;
- optional UI works;
- evaluation harness passes;
- artifact receipts are complete;
- no compliance overclaim appears in README/UI;
- all fixtures are synthetic;
- every unsafe fixture fails closed.
