# RedaktSafe End-to-End Application Goal

/goal

STATUS UPDATE 2026-06-15:
The RedaktSafe local MVP has been implemented and verified in `/Volumes/WS4TB/RedaktSafe`.

Current verified state:

- Git repository initialized after documenting that the folder began as a handoff workspace.
- `redaktsafe_codex_handoff/` remains preserved as source documentation.
- Python package and CLI named `redaktsafe` implemented.
- Deterministic local redaction, packet generation, schema export, evaluation harness, external benchmark adapters, FastAPI service, static local UI, adapter stubs, fake model hook, and benchmark payload helper implemented.
- Generated local run artifacts are gitignored through `.redaktsafe_runs/`.
- Default operation requires no API keys, credentials, model downloads, GPU, cloud service, or external network calls.

Latest verification evidence:

- `python -m pytest` -> 35 passed.
- `python -m redaktsafe.cli doctor` -> status ok.
- `redaktsafe doctor` -> status ok.
- `python -m redaktsafe.cli schemas --out /tmp/redaktsafe-schemas` -> wrote 7 schemas.
- `python -m redaktsafe.cli packet fixtures/synthetic/simple_identifiers.txt --out /tmp/redaktsafe-simple` -> wrote all required artifacts and returned `NEEDS_MANUAL_REVIEW`.
- `python -m redaktsafe.cli packet fixtures/synthetic/high_risk_mixed_identifiers.txt --out /tmp/redaktsafe-risk --strict` -> wrote all required artifacts and returned strict-mode code `3` with risk lane `NOT_LLM_SAFE`.
- Receipt raw-hit inspection for the simple and high-risk runs -> no checked raw identifiers found in `receipt.json`.
- `python -m redaktsafe.cli eval --fixtures evals/cases.jsonl --out /tmp/redaktsafe-eval` -> 10 cases, recall 1.0, precision 1.0, false positives 0, unsafe-pass count 0, artifact completeness 1.0, receipt completeness 1.0, no raw input violations 0.
- `python -m redaktsafe.cli benchmark list` -> listed optional adapters for NVIDIA Nemotron-PII, AI4Privacy PII Masking 300k, Kaggle/PIILO PII Data Detection, Presidio-style synthetic exports, and n2c2/i2b2 2014 de-identification exports.
- `python -m redaktsafe.cli benchmark run --source presidio_synthetic --input /tmp/redaktsafe-presidio-bench-sample.jsonl --out /tmp/redaktsafe-benchmark-presidio` -> local sample benchmark ran with recall 1.0, precision 1.0, false positives 0, unsafe-pass count 0, artifact completeness 1.0, receipt completeness 1.0, no raw input violations 0.
- API/UI served locally at `http://127.0.0.1:8765/`; `/health` returned healthy status.
- Desktop and mobile UI smoke tests passed using local Chrome Beta through Playwright.
- Safety phrase check found no forbidden compliance or safety overclaims in README, docs, frontend, or generated default artifacts.
- Clean-copy install/smoke proof passed in `/tmp/redaktsafe-clean-copy`.
- `git diff --check` exited 0.

Residual/deferred work:

- Real OpenMed, redaktorg, Agent Pidgin, Sentinel, and MLX integrations remain optional deferred work represented by stubs.
- Full external benchmark dataset downloads are user-managed and not part of default tests.
- The UI is a local static workbench, not a production deployment.
- The detector baseline is deterministic and synthetic-fixture-oriented; users must validate against their own data and policies before operational use.

OUTCOME:
Build RedaktSafe Trust Packet Workbench into an end-to-end working local application in `/Volumes/WS4TB/RedaktSafe` so that a user can install it from a clean checkout, process synthetic/deidentified-style text locally, review redaction and residual-risk results, download packet/receipt artifacts, and run the verification suite without API keys, real PHI, cloud calls, or compliance overclaims.

The completed application must include:

1. A Python package and CLI named `redaktsafe`.
2. A deterministic local redaction and packet pipeline.
3. Schema-backed artifacts:
   - `redacted.txt`
   - `safe_packet.json`
   - `redaction_report.json`
   - `receipt.json`
   - `receipt.md`
   - `validation_summary.json`
4. A synthetic fixture and evaluation harness with explicit recall, precision, false-positive, unsafe-pass, latency, artifact-completeness, and no-raw-receipt checks.
5. A local FastAPI service with scoped artifact access.
6. A minimal local browser UI for paste/upload, preflight review, risk lane display, redacted text review, entity summary, limitations, and artifact downloads.
7. Optional adapter architecture for OpenMed, redaktorg, Agent Pidgin, Sentinel, and local model detectors, with deterministic baseline still working when adapters are absent.
8. Documentation that explains installation, local use, safety boundaries, limitations, and how to validate results.

PROOF OF DONE:
1. Repository setup:
   - Confirm `/Volumes/WS4TB/RedaktSafe` is a git repository, or initialize it only after documenting that it was previously just a handoff folder.
   - Confirm `redaktsafe_codex_handoff/` remains preserved as source documentation unless explicitly superseded by a committed design decision.
   - Confirm generated local run artifacts are gitignored.

2. Install and package proof:
   - Run `python -m pytest` and confirm it exits 0.
   - Run `python -m redaktsafe.cli doctor` and confirm it exits 0.
   - Run the installed console command `redaktsafe doctor` if packaging exposes it; otherwise document the exact local command until packaging is complete.
   - Run `python -m redaktsafe.cli schemas --out /tmp/redaktsafe-schemas` and confirm schemas are written.

3. CLI packet proof:
   - Run `python -m redaktsafe.cli packet fixtures/synthetic/simple_identifiers.txt --out /tmp/redaktsafe-simple` and confirm all required artifacts exist.
   - Run `python -m redaktsafe.cli packet fixtures/synthetic/high_risk_mixed_identifiers.txt --out /tmp/redaktsafe-risk --strict` and confirm the command fails closed or returns the documented strict-mode nonzero status while still writing inspectable artifacts when safe to do so.
   - Inspect `/tmp/redaktsafe-simple/receipt.json` and `/tmp/redaktsafe-risk/receipt.json` and confirm neither contains raw input text or original redacted span values.
   - Inspect `safe_packet.json` and confirm it contains only redacted text, structured sections, residual-risk information, limitations, allowed/disallowed downstream uses, and a receipt pointer.

4. Evaluation proof:
   - Run `python -m redaktsafe.cli eval --fixtures evals/cases.jsonl --out /tmp/redaktsafe-eval` and confirm it exits 0.
   - Confirm `/tmp/redaktsafe-eval/eval_results.json` and `/tmp/redaktsafe-eval/eval_report.md` exist.
   - Confirm the eval report includes recall, precision, false positives, unsafe-pass count, latency, receipt completeness, and no-raw-input violations.
   - Confirm unsafe-pass count is 0 on bundled high-risk fixtures.
   - Include at least 10 synthetic regression fixtures covering: simple identifiers, duplicate EHR scaffold, clinical false positives, doctor-vs-patient name ambiguity, date/phone ambiguity, clean no-PHI text, hidden footer identifier, unsafe cloud-export intent, OCR-like noise, and mixed research intake.

5. API proof:
   - Run API tests through `python -m pytest tests` and confirm `/health`, `/api/preflight`, `/api/packet`, and `/api/artifacts/{run_id}/{artifact_name}` behavior is covered.
   - Start the local API with the documented command, then verify:
     - `GET /health` returns healthy status.
     - `POST /api/preflight` returns a transient report without writing arbitrary files.
     - `POST /api/packet` writes only scoped artifacts into the configured local run directory.
     - Artifact route blocks `..`, absolute paths, symlink escapes, unrecognized artifact names, and arbitrary local file reads.
     - Input size limits are enforced.

6. UI proof:
   - Run the documented local UI command.
   - Verify in a browser or automated smoke test that a user can paste synthetic text, run local preflight, see risk lane and warnings, review redacted text, inspect entity summary/receipt/limitations, and download artifacts.
   - Confirm the UI uses local API endpoints only and contains no analytics, external telemetry, remote model calls, or compliance-overclaim text.

7. Safety and provenance proof:
   - Run a grep/check script or documented command that confirms README, docs, UI text, and generated default artifacts do not claim:
     - `HIPAA compliant`
     - `guaranteed deidentified`
     - `safe to share externally`
     - `clinically validated`
     - `production ready`
     - `regulatory cleared`
   - Confirm every generated packet and receipt includes residual-risk and review-required language.
   - Confirm default logs do not include raw input, original spans, secrets, or patient-like identifiers.
   - Confirm no test, fixture, screenshot, or doc example contains real PHI.

8. Adapter proof:
   - Implement adapter interfaces or stubs only after deterministic CLI, eval, API, and UI are working.
   - Add tests proving the app still works when OpenMed, redaktorg, Agent Pidgin, Sentinel, MLX, or model backends are absent.
   - If an OpenMed adapter is implemented, make it opt-in, record model/package metadata in receipts, and prove it cannot downgrade deterministic findings or mark uncertain output safe.
   - Do not require model downloads, Hugging Face access, API keys, GPU, MLX, or external repos for the default test suite.

9. Final repo proof:
   - Run `git diff --check` and confirm it exits 0.
   - Run `git status --short` and provide a changed-file summary.
   - Provide final command output summaries for every verification command above.
   - If feasible, perform a clean-clone or clean-copy install/smoke test and document the commands and results.

SCOPE:
- Modify/create only files needed for the RedaktSafe app under `/Volumes/WS4TB/RedaktSafe`, including:
  - `pyproject.toml`
  - `README.md`
  - `.gitignore`
  - `src/redaktsafe/**`
  - `tests/**`
  - `fixtures/synthetic/**`
  - `evals/**`
  - `schemas/**`
  - `docs/**`
  - `frontend/**`
  - `GOAL.md`
  - `STANDARDS.md`
  - `IMPLEMENT.md`
  - `DECISIONS.md`
  - `PROGRESS.md`
  - `TASK_QUEUE.md`
- Read/reference:
  - `redaktsafe_codex_handoff/README_CODEX_HANDOFF.md`
  - `redaktsafe_codex_handoff/CODEX.md`
  - `redaktsafe_codex_handoff/docs/*.md`
  - `redaktsafe_codex_handoff/tasks/codex_task_queue.yml`
  - `redaktsafe_codex_handoff/schemas/*.json`
  - `redaktsafe_codex_handoff/evals/cases.jsonl`
  - `redaktsafe_codex_handoff/fixtures/synthetic/*.txt`
  - OpenMed and redaktorg documentation or local repos only as optional adapter references.
- Preserve:
  - `redaktsafe_codex_handoff/**` as source documentation unless copying selected fixtures/schemas into canonical app locations.
  - Existing user-created files not directly related to this build.
- Do not modify external repos or sibling projects unless the user explicitly changes the implementation target.

CONSTRAINTS:
- Local-first by default.
- No default network calls.
- No API keys or credentials required for default install, tests, CLI, API, or UI.
- No real PHI, patient data, secrets, credentials, private keys, or sensitive user data in fixtures, tests, docs, generated examples, logs, screenshots, or receipts.
- Do not claim HIPAA compliance, clinical validation, production readiness, regulatory clearance, guaranteed deidentification, or external-sharing safety.
- Do not provide diagnosis, treatment, dosing, disposition, patient-care instructions, clinical recommendations, or patient-specific medical advice.
- Deterministic redaction baseline must work without OpenMed, redaktorg, MLX, Hugging Face, GPU, Docker, external services, or model downloads.
- Optional model/adapters may increase recall but must never override, remove, downgrade, or weaken deterministic structured-identifier findings.
- Fail closed on detector failure, adapter failure, uncertainty, unsafe export intent, high residual risk, path-safety violations, input-size violations, or malformed artifacts.
- Do not remove or weaken tests, fixtures, safety checks, warnings, schemas, receipts, or risk lanes to make commands pass.
- Do not perform broad cleanup, unrelated refactors, marketing-site work, cloud deployment, auth, database integration, live EHR integration, or production deployment inside this goal.
- Add dependencies only when they directly support the scoped app. Justify each dependency in `DECISIONS.md` or `PROGRESS.md`.
- Keep all generated run artifacts in gitignored local output directories such as `.redaktsafe_runs/` or explicit `/tmp/redaktsafe-*` paths.

SAFETY / PROVENANCE:
- Treat this as a PHI-adjacent, safety/provenance-sensitive application.
- Separate implemented behavior from future/deferred behavior in docs and UI.
- Preserve evidence receipts, artifact hashes, detector metadata, adapter metadata, config hashes, model identifiers, risk lanes, and warnings.
- Receipts must not include raw input, original span values, secrets, or raw unredacted text.
- Redaction reports may include offsets, replacement tokens, entity types, detector provenance, confidence, severity, and span hashes, but not raw original spans by default.
- Every output that may leave the preflight layer must include residual-risk language and review-required warnings.
- If a useful idea is outside scope, document it as deferred instead of partially implementing it.
- Prefer explicit uncertainty over fake completeness.
- Document all assumptions made during autonomous work in `PROGRESS.md`.
- Document material architecture, dependency, adapter, safety, or product-scope decisions in `DECISIONS.md`.

ITERATION:
1. Before editing app code, inspect the current root, handoff package, and existing files. Record the discovered state in `PROGRESS.md`.
2. Convert the handoff into repo source-of-truth files first:
   - `STANDARDS.md`
   - `IMPLEMENT.md`
   - `DECISIONS.md`
   - `PROGRESS.md`
   - `TASK_QUEUE.md`
   Keep these concise and grounded in the handoff.
3. Work in dependency order:
   - Phase 0: repo/package bootstrap, fixtures, README, doctor command.
   - Phase 1: contracts, schemas, deterministic detectors, dedup/profile, span merge/redaction, receipt skeleton.
   - Phase 2: packet pipeline, artifact writer, CLI, strict mode.
   - Phase 3: evaluation harness and 10-fixture regression suite.
   - Phase 4: local FastAPI service and path/input/log safety tests.
   - Phase 5: minimal local UI and smoke verification.
   - Phase 6: optional adapter interfaces and graceful-fallback tests.
   - Phase 7: optional OpenMed/model adapter evaluation hooks, only if the baseline app is already passing.
4. After each phase:
   - Run the nearest relevant tests.
   - Update `PROGRESS.md` with commands run, pass/fail results, changed files, known risks, and next step.
   - Update `DECISIONS.md` for material decisions.
   - Do not proceed to later phases if core safety gates are failing.
5. Use small batches. If verification fails, diagnose and repair before expanding scope.
6. If a dependency or tool needs network access, first try the local environment. If network is genuinely required, request approval and document why.
7. If Claude Code is available and useful, delegate only bounded read-only review, test-gap analysis, or loophole search. Codex remains the decision-maker. Do not pass secrets, PHI, credentials, or broad repo-edit authority.

STOP:
Pause and summarize instead of continuing if:
- Real PHI, secrets, credentials, private keys, or sensitive data are discovered in the repo, fixtures, examples, docs, logs, or generated artifacts.
- A required credential, account, API key, model license, private dependency, or external service is needed for the default app.
- A production deployment, cloud upload, live EHR integration, or external data transmission would be required.
- The same verification failure persists after 3 distinct repair attempts.
- Tests require weakening safety behavior, removing warnings, accepting raw-input leakage, or ignoring unsafe-pass cases.
- A product decision would materially change scope, such as making OpenMed mandatory, changing from local-first to cloud-first, adding clinical advice, or targeting compliance certification.
- The needed change would modify unrelated repos, destructive git state, or user-owned files outside the scoped app.
- Legal/compliance uncertainty appears that cannot be safely handled by conservative product language and local-only behavior.

COMPLETE:
Mark the goal complete only when:
1. Every applicable PROOF OF DONE item has passed using actual command output or file inspection evidence.
2. The deterministic CLI, eval harness, local API, and minimal UI all work locally on synthetic fixtures.
3. Default operation requires no network, no credentials, no real PHI, no model download, and no external services.
4. Required artifacts are generated, schema-valid, hash-linked, reviewable, and free of raw input in receipts.
5. High-risk fixtures fail closed or are marked not safe for downstream LLM use.
6. Safety/provenance language is present and compliance overclaims are absent.
7. `PROGRESS.md` and `DECISIONS.md` reflect the final state, residual risks, verification commands, and deferred work.
8. `git diff --check` is clean and the final response includes a concise changed-file summary plus verification evidence.

ASSUMPTIONS:
- `/Volumes/WS4TB/RedaktSafe` is the canonical target workspace for the new app.
- `redaktsafe_codex_handoff/` is source documentation, not the runtime app.
- The first complete version should prioritize a deterministic baseline, receipts, evaluation, and local UI before optional model work.
- OpenMed and `OpenMed/Ministral-3B-PII-Preview` are valuable optional detector/model backends, but must not be mandatory for the default MVP.
- "End-to-end working application" means local CLI + API + UI + eval + artifacts + docs, not production deployment or compliance certification.
