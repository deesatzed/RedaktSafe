# RedaktSafe Trust Packet Workbench — Codex Handoff Package

Date: 2026-06-15
Status: Build handoff for an MVP that is needs-based, local-first, safety-first, and measurable.

## Working product name

**RedaktSafe Trust Packet Workbench**

## One-line product

A local app and SDK that turns messy clinical, research, or AI-workflow text into a redacted, deduplicated, structured, reviewable, LLM-safe packet with a reconstructable receipt.

## Why this exists

The user need is not "smaller local models." The user need is: sensitive text and AI/agent workflows are being handled without reliable preflight, without clear safety boundaries, and without durable proof of what happened.

This MVP targets the clearest wedge: **safe local preparation of sensitive clinical/research text before any downstream AI, research, governance, or agent workflow touches it.**

## Non-negotiable boundaries

1. Local-first by default: raw input must never be sent externally.
2. No bundled PHI or real patient data. Fixtures must be synthetic or public-style only.
3. Do not claim HIPAA compliance, clinical validation, production readiness, or regulatory clearance.
4. The tool can support compliance workflows, but it is not a compliance guarantee.
5. The app must not provide diagnosis, treatment, dosing, disposition, or patient-care instructions.
6. Small models may classify, extract, route, compress, and draft structured fields; deterministic policy validates and receipts.
7. Failing closed is preferred over unsafe pass-through.
8. All outputs that leave the preflight layer must be labeled with residual risk and receipt metadata.

## What Codex should build first

Build a minimal but real MVP with:

- CLI: `redaktsafe packet input.txt --out outdir`
- Local FastAPI backend
- Optional React/Vite frontend
- Deterministic redaction baseline
- Adapter boundary for `redaktorg`
- Structured safe packet JSON
- Redaction report JSON
- Receipt JSON + Markdown
- Synthetic fixture suite
- Evaluation harness for recall/precision/residual-risk gates
- Zero-network default mode

## Recommended first command for Codex

Read these files in order:

1. `README_CODEX_HANDOFF.md`
2. `docs/00_PRODUCT_DECISION_MEMO.md`
3. `docs/01_PRODUCT_REQUIREMENTS.md`
4. `docs/02_ARCHITECTURE_AND_DATA_FLOW.md`
5. `docs/03_IMPLEMENTATION_SPEC.md`
6. `tasks/codex_task_queue.yml`
7. `docs/07_TESTING_AND_EVAL_PLAN.md`
8. `docs/08_SECURITY_PRIVACY_GOVERNANCE.md`
9. `prompts/CODEX_BOOTSTRAP_PROMPT.md`

Then execute Phase 0 through Phase 2 before attempting optional small-model or UI polish work.

## Success definition

A user can run one local command on synthetic or deidentified-style text and receive:

- a safe packet,
- a redaction report,
- a residual-risk assessment,
- a receipt proving the preparation path,
- a validation summary showing no known unsafe pass on the bundled test suite.

## Repo integration stance

Start as a new app/repo or feature branch to avoid destabilizing existing work. Treat existing repos as source-of-truth patterns and optional adapters:

- `redaktorg`: core redaction/dedup/reorganization logic and PHI-safety ordering.
- `Agent_Pidgeon`: semantic contracts, receipts, policy, and trace concepts.
- `sentinel_arbiter`: future governance replay and warranted-yet review module.
- `loclM3`: local MLX model cockpit patterns and UI/backend approach.
- `medical-autoXcon`: future domain router patterns.
- `tuhs-honest-broker`, `onco_snp_nutra`, `aXc-ace-forecaster`, `codebase-archaeology`: future vertical workflows and proof-of-utility targets.

## Build philosophy

Do not build a cool demo. Build a tool someone would use this week because it removes a concrete risk or manual burden.
