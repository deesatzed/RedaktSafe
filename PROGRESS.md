# RedaktSafe Progress

## 2026-06-15 Initial State

Discovered state:

- Working directory: `/Volumes/WS4TB/RedaktSafe`.
- Git state before build: not a git repository.
- Source-of-truth file present at root: `GOAL.md`.
- Standing project files initially missing at root: `STANDARDS.md`, `IMPLEMENT.md`, `DECISIONS.md`, `PROGRESS.md`, and `TASK_QUEUE.md`.
- Handoff package present and preserved: `redaktsafe_codex_handoff/`.
- Handoff docs reviewed for this pass:
  - `redaktsafe_codex_handoff/README_CODEX_HANDOFF.md`
  - `redaktsafe_codex_handoff/CODEX.md`
  - `redaktsafe_codex_handoff/docs/00_PRODUCT_DECISION_MEMO.md`
  - `redaktsafe_codex_handoff/docs/01_PRODUCT_REQUIREMENTS.md`
  - `redaktsafe_codex_handoff/docs/02_ARCHITECTURE_AND_DATA_FLOW.md`
  - `redaktsafe_codex_handoff/docs/03_IMPLEMENTATION_SPEC.md`
  - `redaktsafe_codex_handoff/docs/04_BUILD_PLAN_AND_MILESTONES.md`
  - `redaktsafe_codex_handoff/docs/07_TESTING_AND_EVAL_PLAN.md`
  - `redaktsafe_codex_handoff/docs/08_SECURITY_PRIVACY_GOVERNANCE.md`
  - `redaktsafe_codex_handoff/docs/09_UI_UX_SPEC.md`
  - `redaktsafe_codex_handoff/prompts/CODEX_BOOTSTRAP_PROMPT.md`
  - `redaktsafe_codex_handoff/tasks/codex_task_queue.yml`

Assumptions:

- This folder is the canonical implementation target.
- The handoff package is source documentation, not runtime code.
- It is safe and in-scope to initialize git after documenting the initial handoff-folder state.
- The first implementation batch should prioritize Phase 0 through Phase 2.

Commands run:

- `pwd && rg -n "RedaktSafe|Redakt Safe|redaktsafe" /Users/o2satz/.codex/memories/MEMORY.md` -> no memory hits for this repo name.
- `git status --short --branch` -> failed because the folder was not a git repository.
- `find . -maxdepth 3 -name .git -type d -print` -> no nested git repo found.
- `rg --files -g 'AGENTS.md' -g 'GOAL.md' -g 'STANDARDS.md' -g 'IMPLEMENT.md' -g 'DECISIONS.md' -g 'PROGRESS.md' -g 'TASK_QUEUE.md'` -> only `GOAL.md` was present before this batch.

Next step:

- Initialize git, add Phase 0 package files, copy/adapt synthetic fixtures, and start tests for the CLI baseline.

## 2026-06-15 Build Progress

Implemented:

- Initialized git after documenting the initial non-repo state.
- Added concise repo control files: `STANDARDS.md`, `IMPLEMENT.md`, `DECISIONS.md`, `PROGRESS.md`, and `TASK_QUEUE.md`.
- Added package metadata, editable install support, and console script configuration in `pyproject.toml`.
- Added deterministic package code under `src/redaktsafe/`.
- Added CLI commands: `doctor`, `schemas`, `packet`, `text`, `eval`, and `serve`.
- Added Pydantic contracts and schema export.
- Added deterministic detectors, span merge, exact-line dedup, input profile, redaction, packet pipeline, and artifact writer.
- Added 10 synthetic regression fixtures and `evals/cases.jsonl`.
- Added local FastAPI service with `/health`, `/api/preflight`, `/api/packet`, and scoped artifact access.
- Added static local browser UI under `frontend/`.
- Added optional adapter protocol and unavailable stubs for OpenMed, redaktorg, Agent Pidgin, Sentinel, and MLX/local model backends.
- Added fake local model adapter test hook and benchmark payload helper.

Verification passed:

- `python -m pip install -e . --no-deps` -> installed local editable package. Pip emitted an unrelated warning about an invalid `~ecret-sweep` distribution in the active environment.
- `python -m pytest` -> 28 passed.
- `python -m redaktsafe.cli doctor` -> status ok, no network required, no credentials required.
- `redaktsafe doctor` -> status ok, no network required, no credentials required.
- `python -m redaktsafe.cli schemas --out /tmp/redaktsafe-schemas` -> wrote 7 schemas.
- `python -m redaktsafe.cli packet fixtures/synthetic/simple_identifiers.txt --out /tmp/redaktsafe-simple` -> wrote all 6 required artifacts, risk lane `NEEDS_MANUAL_REVIEW`.
- `python -m redaktsafe.cli packet fixtures/synthetic/high_risk_mixed_identifiers.txt --out /tmp/redaktsafe-risk --strict` -> returned strict status `3`, wrote all 6 required artifacts, risk lane `NOT_LLM_SAFE`.
- Receipt inspection for `/tmp/redaktsafe-simple/receipt.json` and `/tmp/redaktsafe-risk/receipt.json` -> no checked raw identifier hits.
- Safe packet inspection -> includes redacted text, residual risk, limitations, allowed/disallowed uses, and receipt pointer.
- `python -m redaktsafe.cli eval --fixtures evals/cases.jsonl --out /tmp/redaktsafe-eval` -> 10 cases, recall 1.0, precision 1.0, false positives 0, unsafe-pass count 0, artifact completeness 1.0, receipt completeness 1.0, no raw input violations 0.
- Local API health check at `http://127.0.0.1:8765/health` -> 200 healthy.
- API tests cover health, transient preflight, scoped packet writes, artifact serving, traversal blocking, unknown artifact blocking, symlink escape blocking, and input-size enforcement.
- UI tests cover required workflow text, local relative API calls, no remote URLs in `frontend/app.js`, and static asset serving.
- Local UI smoke via Chrome Beta and Playwright -> demo preflight reached `NOT_LLM_SAFE`, redacted text included `[REDACTED_NAME]`, 6 artifact download links rendered.
- Mobile UI smoke at 390px width -> `NOT_LLM_SAFE`, no horizontal overflow.

## 2026-06-15 Final Verification Evidence

Final verification passed:

- `python -m pytest` -> 28 passed.
- `git diff --check` -> exited 0.
- Safety phrase check across `README.md`, `docs/`, `frontend/`, `/tmp/redaktsafe-simple`, `/tmp/redaktsafe-risk`, and `/tmp/redaktsafe-eval` -> `forbidden_claim_hits= []`.
- Clean-copy proof:
  - Copied repo to `/tmp/redaktsafe-clean-copy` excluding `.git`, `.redaktsafe_runs`, `__pycache__`, and `.pytest_cache`.
  - Created `/tmp/redaktsafe-clean-venv` with system site packages.
  - Installed editable clean copy with `--no-deps`.
  - `/tmp/redaktsafe-clean-venv/bin/python -m pytest /tmp/redaktsafe-clean-copy -q` -> 28 passed.
  - `/tmp/redaktsafe-clean-venv/bin/python -m redaktsafe.cli doctor` -> status ok.
  - Clean-copy packet smoke on `simple_identifiers.txt` -> wrote 6 artifacts and returned `NEEDS_MANUAL_REVIEW`.
- Final CLI proof:
  - `python -m redaktsafe.cli doctor` -> status ok.
  - `redaktsafe doctor` -> status ok.
  - `python -m redaktsafe.cli schemas --out /tmp/redaktsafe-schemas` -> wrote 7 schemas.
  - `python -m redaktsafe.cli packet fixtures/synthetic/simple_identifiers.txt --out /tmp/redaktsafe-simple` -> wrote 6 artifacts, risk lane `NEEDS_MANUAL_REVIEW`.
  - `python -m redaktsafe.cli packet fixtures/synthetic/high_risk_mixed_identifiers.txt --out /tmp/redaktsafe-risk --strict` -> wrote 6 artifacts, risk lane `NOT_LLM_SAFE`, strict return code `3`.
  - Receipt raw-hit inspection for simple and risk receipts -> no checked raw identifier hits.
  - `python -m redaktsafe.cli eval --fixtures evals/cases.jsonl --out /tmp/redaktsafe-eval` -> 10 cases, recall 1.0, precision 1.0, false positives 0, unsafe-pass count 0, artifact completeness 1.0, receipt completeness 1.0, no raw input violations 0.
- Local service:
  - `python -m redaktsafe.cli serve --host 127.0.0.1 --port 8765` served the API/UI.
  - `GET http://127.0.0.1:8765/health` -> 200 healthy.
  - Detached local service restarted as PID `13372`; log path `/tmp/redaktsafe-ui.log`.
- Browser/UI proof:
  - In-app Browser was unavailable in this session, so local Playwright was used with `/Applications/Google Chrome Beta.app/Contents/MacOS/Google Chrome Beta`.
  - Desktop smoke loaded `http://127.0.0.1:8765/`, used synthetic demo, ran local preflight, reached `NOT_LLM_SAFE`, rendered `[REDACTED_NAME]`, and showed 6 artifact download links.
  - Desktop screenshot saved to `/tmp/redaktsafe-ui-smoke.png`.
  - Mobile smoke at 390px width reached `NOT_LLM_SAFE` and had no horizontal overflow.
  - Mobile screenshot saved to `/tmp/redaktsafe-ui-mobile-smoke.png`.

Residual risks and deferred work:

- Optional real OpenMed, redaktorg, Agent Pidgin, Sentinel, and MLX integrations are stubs only. This is intentional; default operation remains deterministic and local.
- The UI is static and local-first, not a production deployment.
- The detector baseline is deterministic and synthetic-fixture-oriented; users still need to validate against their own data and policies.

## 2026-06-16 External PII Benchmark Adapters

Implemented:

- Added `src/redaktsafe/benchmarks.py`.
- Added `redaktsafe benchmark list`.
- Added `redaktsafe benchmark run --source SOURCE --input PATH --out PATH [--limit N]`.
- Added benchmark registry entries for:
  - `nemotron_pii`
  - `ai4privacy_300k`
  - `kaggle_pii`
  - `presidio_synthetic`
  - `n2c2_2014_deid`
- Added local export loaders for JSONL/JSON span datasets, Kaggle token-label JSON, and simple n2c2-style XML.
- Added `docs/BENCHMARKS.md`.

Safety posture:

- Benchmark datasets are user-provided local inputs.
- RedaktSafe does not download benchmark datasets automatically.
- Default tests remain offline and credential-free.

Verification so far:

- `python -m pytest tests/test_benchmarks.py -q` -> 7 passed.
- `python -m pytest` -> 35 passed.
- `python -m redaktsafe.cli benchmark list` -> listed 5 supported benchmark adapters.
- `python -m redaktsafe.cli benchmark run --source presidio_synthetic --input /tmp/redaktsafe-presidio-bench-sample.jsonl --out /tmp/redaktsafe-benchmark-presidio` -> 1 local sample case, recall 1.0, precision 1.0, false positives 0, unsafe-pass count 0, no raw input violations 0.
- Live Hugging Face sample check for `nemotron_pii`:
  - Pulled 5 rows through the Hugging Face datasets server into `/tmp/redaktsafe-nemotron-sample.jsonl`.
  - `python -m redaktsafe.cli benchmark run --source nemotron_pii --input /tmp/redaktsafe-nemotron-sample.jsonl --out /tmp/redaktsafe-benchmark-nemotron-live` -> case count 5, recall 1.0, precision 0.0, false positives 7, unsafe-pass count 0, artifact completeness 1.0, receipt completeness 1.0, no raw input violations 0.
  - Interpretation: the live Nemotron sample includes labels outside RedaktSafe's current core entity families, so this is a coverage-gap signal rather than a release blocker.
- Live Hugging Face sample check for `ai4privacy_300k`:
  - Pulled 5 validation rows through the Hugging Face datasets server into `/tmp/redaktsafe-ai4privacy-sample.jsonl`.
  - `python -m redaktsafe.cli benchmark run --source ai4privacy_300k --input /tmp/redaktsafe-ai4privacy-sample.jsonl --out /tmp/redaktsafe-benchmark-ai4privacy-live` -> case count 5, recall 1.0, precision 1.0, false positives 0, unsafe-pass count 0, artifact completeness 1.0, receipt completeness 1.0, no raw input violations 0.
- Kaggle/PIILO and n2c2/i2b2 were not downloaded or run live because they require user-managed account/terms or access-controlled clinical dataset handling.
- `git diff --check` -> exited 0.
- Standard CLI/eval proof rerun -> doctor ok, console doctor ok, 7 schemas exported, simple packet `NEEDS_MANUAL_REVIEW`, high-risk strict packet `NOT_LLM_SAFE` with strict return code `3`, eval recall 1.0, precision 1.0, unsafe-pass count 0.
- Receipt raw-hit inspection for simple and high-risk runs -> no checked raw identifier hits.
- Contextual safety phrase check -> no forbidden claim violations.

## 2026-06-16 Real Hugging Face Model Detector

Implemented:

- Added `hf_token_classifier` adapter using local Hugging Face token-classification models.
- Added optional `models` dependency extra for real model detection.
- Added CLI support for `--hf-model-id` and `--hf-min-score` on packet/text and benchmark commands.
- Added `.env` support for `HF_TOKEN`, `HUGGING_FACE_HUB_TOKEN`, and `HF_READ`.
- Added model adapter tests with an injected fake pipeline so default tests remain offline.
- Added adapter caching so benchmark runs load a model once per process instead of once per case.

Environment findings:

- `.env` contains `HF_READ`; token validation identified the Hugging Face account as `o2satz`.
- Active Python environment had `transformers`, `torch`, and `huggingface_hub`.
- `kernels 0.15.1` caused a `ValueError: Either a revision or a version must be specified` during transformer model imports. Downgrading to `kernels 0.14.1` fixed the issue.

Verification:

- `python -m pytest` -> 38 passed.
- `python -m redaktsafe.cli text 'Consult completed for Avery Stone. Email jane@example.com. Phone 617-555-0142.' --out /tmp/redaktsafe-hf-openmed-env-smoke2 --hf-model-id OpenMed/OpenMed-PII-SuperClinical-Large-434M-v1 --hf-min-score 0.20` -> wrote 6 artifacts and detected `NAME`, `EMAIL`, and `PHONE`.
- `python -m redaktsafe.cli benchmark run --source nemotron_pii --input /tmp/redaktsafe-nemotron-sample.jsonl --out /tmp/redaktsafe-benchmark-nemotron-openmed-cached --hf-model-id OpenMed/OpenMed-PII-SuperClinical-Large-434M-v1 --hf-min-score 0.20` -> case count 5, recall 0.9167, precision 1.0, false positives 0, unsafe-pass count 1, no raw input violations 0, p50 latency about 163 ms after adapter caching.
- `python -m redaktsafe.cli benchmark run --source ai4privacy_300k --input /tmp/redaktsafe-ai4privacy-sample.jsonl --out /tmp/redaktsafe-benchmark-ai4privacy-openmed --hf-model-id OpenMed/OpenMed-PII-SuperClinical-Large-434M-v1 --hf-min-score 0.20` -> case count 5, recall 0.2, precision 0.3333, false positives 2, unsafe-pass count 1, no raw input violations 0.

## 2026-06-16 Drift Check Against OpenMed Comparison

Finding:

- No material implementation drift from the initial directives was found. The project goal explicitly required deterministic local redaction, schema-backed artifacts, eval metrics, local API/UI, and optional OpenMed/model adapters that remain additive and opt-in.
- The main drift found was documentation drift: `README.md` still described API, UI, and adapters as future work after those parts had been implemented. The status text was updated to match the verified app state.

Current product distinction:

- OpenMed is the stronger raw model detector/runtime layer.
- RedaktSafe is the local trust-packet workbench around detection: deterministic baseline, optional model findings, redacted artifacts, receipts, residual-risk language, strict fail-closed behavior, local API/UI, scoped artifact downloads, and benchmark/eval reporting.

Fresh verification:

- `python -m pytest -q` -> 38 passed.
- `git diff --check` -> exited 0.

## 2026-06-16 Learning Loop First Slice

Implemented:

- Added opt-in learning contracts for correction type, context category, review route, correction records, and queue items.
- Added error-severity scoring that ranks the expected cost of an additional classification error from entity sensitivity, error type, context, downstream exposure, detector disagreement, and recurrence.
- Added review routing for `REVIEW_REDACT`, `REVIEW_ALLOW`, and `AUTO_ALLOW_WITH_TRACE`; high-risk false negatives route to human review.
- Added encrypted local snippet retention under `.redaktsafe_learning/` with correction JSONL records storing hashes and metadata rather than plaintext snippets.
- Added `redaktsafe learning add-correction` and `redaktsafe learning queue`.

Safety posture:

- Learning mode is off by default.
- `.redaktsafe_learning/` is gitignored.
- Correction ledgers do not store raw snippets or span text.
- The first learning slice does not auto-promote rules, change packet detector behavior, or fine-tune models.

Verification:

- `python -m pytest tests/test_learning.py -q` -> 9 passed.
- `python -m pytest -q` -> 47 passed.
- `git diff --check` -> exited 0.

## 2026-06-16 Learning Audit, Promotion Gates, and Fine-Tuning Export

Implemented:

- Added `redaktsafe learning audit --if-due --interval-hours 24`.
- Added audit state tracking that skips when there is no learning activity or no new activity since the last audit.
- Added audit artifacts: `audit_report.json` and `audit_report.md`.
- Added context canaries covering:
  - `DeVries syndrome` medical eponym context,
  - `Patient DeVries` patient identifier context,
  - `Johns Hopkins` institution context,
  - `East Tower` building/unit context,
  - `DeVries Lab` research lab context.
- Added shadow-mode candidate mitigations with source correction IDs, context category, severity score, gate results, promotion decision, version, and rollback reference.
- Added `redaktsafe learning canaries --out PATH`.
- Added `redaktsafe learning export-finetune --dry-run`, with readiness blocked until the reviewed correction count reaches the configured minimum.

Safety posture:

- Candidate mitigations remain advisory and `promote=false` by default.
- High-risk false negatives route to human review and are not auto-promoted.
- Fine-tuning export does not run real training and reports `insufficient_reviewed_corrections` when data volume is below threshold.
- Optional benchmark sample failures block promotion rather than being ignored.

Verification:

- `python -m pytest tests/test_learning.py -q` -> 14 passed.
- `python -m pytest -q` -> 52 passed.
- `python -m redaktsafe.cli schemas --out /tmp/redaktsafe-schemas-final` -> wrote 11 schemas.
- `python -m redaktsafe.cli learning canaries --out /tmp/redaktsafe-learning-canaries-final` -> case count 5, unsafe-pass count 0, wrote JSON and Markdown artifacts.
- Learning smoke with missed MRN and `DeVries syndrome` false-positive corrections -> first queue item was missed `MRN`, route `REVIEW_REDACT`, severity `100`.
- `python -m redaktsafe.cli learning audit --store /tmp/redaktsafe-learning-goal-smoke --out /tmp/redaktsafe-learning-goal-audit-1 --if-due --interval-hours 24` -> ran with new activity count 2, candidate count 2, canaries passed, promotion allowed false.
- Second audit with same store and `--if-due --interval-hours 24` -> skipped with `skip_reason=no_new_activity`.
- `python -m redaktsafe.cli learning export-finetune --store /tmp/redaktsafe-learning-goal-smoke --out /tmp/redaktsafe-learning-goal-finetune --passphrase local-secret --min-examples 3 --dry-run` -> ready false, example count 2, reason `insufficient_reviewed_corrections`.
- Plaintext scan of `/tmp/redaktsafe-learning-goal-smoke` for known snippets -> no hits.
- `python -m redaktsafe.cli eval --fixtures evals/cases.jsonl --out /tmp/redaktsafe-eval-final` -> 10 cases, recall 1.0, precision 1.0, unsafe-pass count 0, no raw input violations 0.
- Packet receipt inspection for simple and high-risk fixtures -> no checked raw identifier hits; high-risk strict packet returned code 3.
- Local benchmark samples:
  - Presidio synthetic sample -> recall 1.0, precision 1.0, unsafe-pass count 0.
  - Nemotron sample -> recall 0.5833, precision 1.0, unsafe-pass count 1.
  - AI4Privacy sample -> recall 0.0, precision 1.0, unsafe-pass count 4.
- Safety phrase scan -> no forbidden claim violations.
