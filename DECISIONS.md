# RedaktSafe Decisions

## 2026-06-15: Treat Current Folder as Handoff Workspace, Then Initialize Repo

Status: Accepted

`/Volumes/WS4TB/RedaktSafe` initially contained `GOAL.md`, `RedaktSafe_Codex_Handoff_Master.docx`, and `redaktsafe_codex_handoff/`, but was not a git repository. The build will document that state in `PROGRESS.md`, preserve `redaktsafe_codex_handoff/` as source documentation, then initialize git in this folder so future changes are trackable.

## 2026-06-15: Deterministic Baseline Is Mandatory

Status: Accepted

The default app will use deterministic local detection and redaction without model downloads, API keys, cloud calls, or external services. Optional adapters may be added later, but they cannot weaken or downgrade deterministic findings.

## 2026-06-15: Receipts Exclude Raw Input and Original Span Values

Status: Accepted

Receipts will store hashes, counts, detector metadata, artifact names, risk lanes, policy findings, warnings, and output hashes. They will not contain raw input text or original redacted values. Redaction reports may include span hashes and offsets, but not raw original spans by default.

## 2026-06-15: Strict Mode Fails Closed

Status: Accepted

The CLI `--strict` mode will return a nonzero status when the risk lane is high, uncertain, not LLM-safe, or pipeline-error fail-closed. When safe to do so, inspectable artifacts should still be written for review.

## 2026-06-15: Static UI Served by Local API

Status: Accepted

The first UI is a static local browser interface under `frontend/` served by the FastAPI app. It uses relative local API calls only and avoids a Node/Vite build requirement for the default install and test path.

## 2026-06-15: Optional Adapters Are Unavailable Stubs Until Explicitly Enabled

Status: Accepted

OpenMed, redaktorg, Agent Pidgin, Sentinel, and MLX/local model integrations are represented by protocol-compatible unavailable stubs. The deterministic baseline remains default and the app works when those backends are absent.

## 2026-06-16: External PII Benchmarks Are Optional Local Inputs

Status: Accepted

RedaktSafe will support standard PII benchmark adapters for local exports from NVIDIA Nemotron-PII, AI4Privacy PII Masking 300k, Kaggle/PIILO PII Data Detection, Presidio-generated samples, and n2c2/i2b2 2014 de-identification data. The app will not automatically download these datasets or require benchmark credentials in default tests. Benchmark commands normalize user-provided local exports into the existing eval harness.

## 2026-06-16: Real Model Detection Is Opt-In and Additive

Status: Accepted

RedaktSafe now supports opt-in Hugging Face token-classification models through `hf_token_classifier`. Model findings are additive: they can add detected spans but cannot remove, override, or downgrade deterministic findings. Tokens may be supplied through `HF_TOKEN`, `HUGGING_FACE_HUB_TOKEN`, or `HF_READ` in the environment or local `.env`; `.env` remains ignored.

## 2026-06-16: Learning Mode Retains Encrypted Local Snippets Only When Explicitly Enabled

Status: Accepted

RedaktSafe learning mode is opt-in and separate from the default packet pipeline. It may retain encrypted local snippets for reviewed corrections until learning work is completed, but the correction ledger stores hashes and review metadata rather than plaintext snippets. Learning mode ranks classification-error severity and routes high-cost or ambiguous cases to human review. The first implementation does not auto-promote rules, change detector behavior, or fine-tune models.

## 2026-06-16: Learning Promotion Requires Shadow Mode, Canaries, and Human Review Gates

Status: Accepted

Learning audits can create candidate mitigations from reviewed corrections, but candidates remain advisory and shadow-mode by default. Each candidate records source correction IDs, context category, severity score, gate results, a promotion decision, version, and rollback reference. Current promotion gates set `promote=false` unless canary/benchmark evidence and human review allow promotion. High-risk false negatives route to human review and are not auto-promoted.

## 2026-06-16: Fine-Tuning Is Export-Gated, Not Automatic

Status: Accepted

RedaktSafe now provides a fine-tuning export/dry-run path for reviewed corrections. It reports readiness only when the reviewed correction count meets the configured minimum. It does not train on unreviewed model guesses, and dry-run output is used when correction volume is insufficient.
