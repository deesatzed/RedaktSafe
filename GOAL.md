# RedaktSafe Remaining Learning Loop Goal

/goal

STATUS UPDATE 2026-06-16:

The RedaktSafe local MVP and first learning-loop slice have already been implemented and pushed in `/Volumes/WS4TB/RedaktSafe`.

Current verified baseline:

- Python package and CLI named `redaktsafe` implemented.
- Deterministic local redaction, opt-in Hugging Face/OpenMed model detection, opt-in encrypted local learning correction capture, packet generation, schema export, evaluation harness, external benchmark adapters, FastAPI service, static local UI, adapter stubs, fake model hook, and benchmark payload helper implemented.
- Default operation remains local-first, deterministic, credential-free, network-free, and model-download-free.
- Learning mode is opt-in and currently supports encrypted local snippet retention, correction ledger, severity scoring, review queue, 24-hour-if-active audit behavior, context canaries, shadow-mode candidate mitigations, promotion gates, and fine-tuning export/dry-run.
- `.redaktsafe_runs/`, `.redaktsafe_learning/`, and `.env` are gitignored.
- Latest pushed commits include:
  - `f908dd7 Add local learning correction loop`
  - `16462d6 Plan RedaktSafe learning loop`
  - `e1af6d4 Document RedaktSafe drift assessment`

Latest verified commands before this remaining-work goal:

- `python -m pytest tests/test_learning.py -q` -> 14 passed.
- `python -m pytest -q` -> 52 passed.
- `python -m redaktsafe.cli schemas --out /tmp/redaktsafe-schemas-final` -> wrote 11 schemas.
- Learning CLI smoke routed a missed MRN correction to `REVIEW_REDACT` with severity `100`.
- Learning audit smoke ran with new activity count 2, candidate count 2, canaries passed, promotion allowed false, then skipped the second run with `skip_reason=no_new_activity`.
- Fine-tuning dry-run reported `ready=false` because reviewed correction count was below the configured minimum.
- Plaintext scan of `/tmp/redaktsafe-learning-goal-smoke` found no raw snippet hits.
- `git diff --check` exited 0.
- Safety phrase scan found no forbidden compliance or safety overclaims.

OUTCOME:
Maintain and verify the completed RedaktSafe learning-loop build so that the app can locally capture reviewed corrections, rank error severity, retain encrypted snippets, run a 24-hour-if-active audit, propose context-aware mitigations, gate learned changes against benchmarks/canaries, prepare a fine-tuning dataset path when enough reviewed data exists, document the final state, commit the work, and push to `https://github.com/deesatzed/RedaktSafe.git`.

PROOF OF DONE:
1. Run `python -m pytest -q` and confirm it exits 0.
2. Run `python -m redaktsafe.cli doctor` and confirm it exits 0.
3. Run `redaktsafe doctor` and confirm it exits 0 if the console command remains installed.
4. Run `python -m redaktsafe.cli schemas --out /tmp/redaktsafe-schemas-final` and confirm learning/audit schemas are exported.
5. Run a learning correction smoke test:
   - add at least one missed direct identifier correction,
   - add at least one eponym or institution false-positive correction,
   - run the learning queue,
   - confirm high-risk missed identifiers route to human review before promotion.
6. Run a learning audit smoke command that supports `--if-due --interval-hours 24` and confirm:
   - no audit runs when no new activity is present,
   - an audit runs when new learning activity exists,
   - audit artifacts are written under a local ignored output directory.
7. Confirm the audit produces:
   - failure summary,
   - model/detector disagreement summary,
   - candidate mitigation list,
   - canary/benchmark gate results,
   - promotion recommendation with `promote=false` unless gates pass.
8. Confirm context canaries cover at minimum:
   - `DeVries syndrome` as medical eponym context,
   - patient surname context such as `Patient DeVries, DOB...`,
   - institution names,
   - building/unit names,
   - research lab names.
9. Confirm encrypted learning stores do not contain raw snippets by scanning the local test store for known raw phrases.
10. Confirm receipts and default packet artifacts still do not include raw input or original span values.
11. Run benchmark/eval gates:
    - bundled synthetic eval,
    - learning canary eval,
    - any available local benchmark samples already present under `/tmp/redaktsafe-*`.
12. Run `git diff --check` and confirm it exits 0.
13. Run the safety phrase scan and confirm there are no forbidden overclaims:
    - `HIPAA compliant`
    - `guaranteed deidentified`
    - `safe to share externally`
    - `clinically validated`
    - `production ready`
    - `regulatory cleared`
14. Update `GOAL.md`, `PROGRESS.md`, `DECISIONS.md`, `TASK_QUEUE.md`, README, and relevant docs with final verified state and deferred work.
15. Commit all in-scope changes with a clear message.
16. Push `main` to `https://github.com/deesatzed/RedaktSafe.git`.
17. Final response must include:
    - commit hash,
    - push result,
    - changed-file summary,
    - verification command summaries,
    - remaining untracked files, especially `I2B2-2014-Relabeled-PhysionetGoldCorpus.csv` if still present.

SCOPE:
- Modify only:
  - `GOAL.md`
  - `STANDARDS.md`
  - `IMPLEMENT.md`
  - `DECISIONS.md`
  - `PROGRESS.md`
  - `TASK_QUEUE.md`
  - `README.md`
  - `.gitignore`
  - `pyproject.toml` only if a dependency is truly required and justified
  - `docs/**`
  - `src/redaktsafe/**`
  - `tests/**`
  - `fixtures/synthetic/**`
  - `evals/**`
- Read/reference:
  - `docs/plans/2026-06-16-learning-loop-design.md`
  - `docs/plans/2026-06-16-learning-loop.md`
  - existing benchmark docs and sample outputs
  - existing Hugging Face/OpenMed adapter code
  - local `.env` only to detect key presence; never print secrets
  - `redaktsafe_codex_handoff/**` as historical source documentation
- Preserve:
  - `redaktsafe_codex_handoff/**`
  - existing public CLI commands unless this goal explicitly extends them
  - existing packet artifact names and receipt safety semantics
  - existing user-created files not directly related to this build
- Do not modify:
  - unrelated repos
  - user-owned benchmark CSV files unless explicitly requested
  - `.env`

CONSTRAINTS:
- Default RedaktSafe operation must remain local-first, deterministic, credential-free, network-free, and model-download-free.
- Learning mode must remain opt-in.
- No raw snippets, PHI-like values, secrets, credentials, private keys, or original span values may appear in receipts, default logs, docs examples, committed tests, screenshots, or generated default artifacts.
- Encrypted snippet retention is allowed only in ignored local learning stores.
- Learned changes must never remove, weaken, override, or downgrade deterministic structured-identifier findings.
- High-risk false negatives must route to human review; do not auto-promote them.
- Do not implement blanket allowlists for bare tokens such as `DeVries`; learn context patterns only.
- Fine-tuning must not run on unreviewed model guesses.
- If there are too few reviewed corrections for real fine-tuning, implement a validated dataset export or dry-run path and document the minimum data requirement.
- Do not claim HIPAA compliance, clinical validation, guaranteed deidentification, regulatory clearance, production readiness, or external-sharing safety.
- Do not provide diagnosis, treatment, dosing, disposition, patient-care instructions, clinical recommendations, or patient-specific medical advice.
- Do not add cloud services, telemetry, analytics, auth, production deployment, live EHR integration, or database infrastructure.
- Do not weaken or delete tests to make the build pass.
- Add dependencies only when they directly support this scoped app and are justified in `DECISIONS.md` or `PROGRESS.md`.

SAFETY / PROVENANCE:
- Treat this as PHI-adjacent, safety/provenance-sensitive software.
- Preserve receipts, hashes, detector metadata, adapter metadata, audit metadata, learned-rule provenance, and rollbackability.
- Receipts must not include raw input, original span values, secrets, or raw unredacted text.
- Every candidate mitigation must record:
  - source correction IDs or hashes,
  - context category,
  - severity score,
  - benchmark/canary result,
  - promotion decision,
  - version identifier.
- Audit and promotion artifacts must separate:
  - observed corrections,
  - model suggestions,
  - candidate mitigations,
  - active learned behavior.
- Every output that may leave the preflight layer must include residual-risk language and review-required warnings.
- If a useful idea is outside scope or cannot be safely implemented, document it as deferred instead of partially implementing it.
- Prefer explicit uncertainty over fake completeness.
- Document all assumptions made during autonomous work in `PROGRESS.md`.
- Document material architecture, dependency, adapter, safety, promotion, storage, or fine-tuning decisions in `DECISIONS.md`.

ITERATION:
1. Before editing app code, inspect current git status, `GOAL.md`, `STANDARDS.md`, `IMPLEMENT.md`, `DECISIONS.md`, `PROGRESS.md`, `TASK_QUEUE.md`, README, learning docs, `src/redaktsafe/learning.py`, CLI, contracts, tests, and benchmark harness.
2. Work in dependency order:
   - Phase 1: audit state model and activity detection.
   - Phase 2: context canary fixtures and canary eval.
   - Phase 3: audit command and audit artifacts.
   - Phase 4: candidate mitigation scoring and shadow-mode representation.
   - Phase 5: promotion gates with rollback/version metadata.
   - Phase 6: fine-tuning export/dry-run path.
   - Phase 7: docs/control-file updates, final verification, commit, and push.
3. Use TDD for new behavior:
   - write failing tests,
   - verify failure,
   - implement minimum code,
   - verify targeted pass,
   - run broader suite.
4. After each batch, update `PROGRESS.md` with commands, results, changed files, known risks, and next step.
5. Update `DECISIONS.md` for material safety, dependency, storage, promotion, audit, or fine-tuning decisions.
6. If a larger local teacher model is available through local/Hugging Face config, support it as optional. Default tests must use fake/injected teacher adapters.
7. Before commit, run full verification and inspect the diff.
8. Commit only in-scope files. Leave `I2B2-2014-Relabeled-PhysionetGoldCorpus.csv` untracked unless explicitly told otherwise.
9. Push to GitHub only after verification passes.

STOP:
Pause and summarize instead of continuing if:
- Real PHI, secrets, private keys, credentials, or sensitive data are found in files that would be committed.
- A required credential, model, license, account, or external service is missing for a non-optional path.
- The same verification failure persists after 3 distinct repair attempts.
- A proposed mitigation would weaken deterministic redaction or increase unsafe-pass behavior.
- Fine-tuning would require unreviewed, sensitive, or insufficient data.
- Tests require weakening safety behavior, removing warnings, accepting raw-input leakage, or ignoring unsafe-pass cases.
- Legal/compliance uncertainty cannot be handled by conservative local-only behavior.
- The task would require production deployment, cloud upload, telemetry, live EHR integration, or modifying unrelated repos.
- The needed change would modify user-owned files outside the scoped app.
- Git push fails due to authentication or remote errors after local commit succeeds.

COMPLETE:
Mark complete only when:
1. Every applicable PROOF OF DONE item has passed using actual command output or file inspection evidence.
2. The default deterministic CLI, eval harness, local API, and local UI still work locally on synthetic fixtures.
3. Learning mode remains opt-in and encrypted local snippet retention is confirmed not to leak plaintext into ledgers, receipts, default logs, or committed artifacts.
4. 24-hour-if-active audit behavior, context canaries, candidate mitigations, promotion gates, and fine-tuning export/dry-run path are implemented or explicitly deferred with evidence-backed reasons.
5. High-risk false negatives route to human review and are not auto-promoted.
6. Safety/provenance language is present and compliance overclaims are absent.
7. `GOAL.md`, `PROGRESS.md`, `DECISIONS.md`, `TASK_QUEUE.md`, README, and relevant docs reflect the final state, residual risks, verification commands, and deferred work.
8. `git diff --check` is clean.
9. The final code/doc changes are committed.
10. `main` is pushed to `https://github.com/deesatzed/RedaktSafe.git`.
11. The final response includes a concise changed-file summary, verification evidence, commit hash, push result, and untracked-file summary.

ASSUMPTIONS:
- `/Volumes/WS4TB/RedaktSafe` is the canonical target repo.
- `redaktsafe_codex_handoff/` is source documentation, not runtime code.
- The current first-slice learning loop is implemented and pushed.
- The next work should finish the remaining learning/audit/promotion/fine-tuning-prep system, not replace the existing app.
- Real fine-tuning is gated on having enough reviewed corrections; dry-run/export is acceptable if reviewed data volume is insufficient.
- `I2B2-2014-Relabeled-PhysionetGoldCorpus.csv` is a local user file and should remain untracked unless the user explicitly requests otherwise.
