# RedaktSafe Learning Loop Implementation Plan

> **For Codex:** REQUIRED SUB-SKILL: Use executing-plans to implement this plan task-by-task.

**Goal:** Add the first safe slice of learning mode: local encrypted snippet retention, reviewed correction capture, contextual error severity scoring, and human-review routing.

**Architecture:** Learning mode is opt-in and isolated from the default packet pipeline. A new `redaktsafe.learning` module stores encrypted snippets and JSONL correction records in a local ignored directory, then computes review routes from entity sensitivity, error type, context category, downstream exposure, detector disagreement, and recurrence. The first slice does not auto-promote rules or fine-tune models.

**Tech Stack:** Python 3.12 standard library, Pydantic v2, pytest, argparse CLI, PBKDF2-HMAC, and an HMAC-derived XOR stream for local snippet encryption until a stronger optional crypto dependency is justified.

---

## Task 1: Add Learning Contracts

**Files:**

- Modify: `src/redaktsafe/contracts.py`
- Test: `tests/test_learning.py`

**Step 1: Write failing tests**

Add tests that construct correction records with:

- `false_negative` on `MRN` in `patient_context` routed to `REVIEW_REDACT`.
- `false_positive` on `NAME` in `medical_eponym` routed to `REVIEW_ALLOW`.
- `contextual_allow` for a medical eponym routed to `AUTO_ALLOW_WITH_TRACE` only when score is low.

**Step 2: Run targeted tests**

Run: `python -m pytest tests/test_learning.py -q`

Expected: failure because learning contracts do not exist.

**Step 3: Implement minimal contracts**

Add enums and models:

- `LearningErrorType`
- `LearningContextCategory`
- `ReviewRoute`
- `LearningCorrection`
- `LearningQueueItem`

**Step 4: Run targeted tests**

Run: `python -m pytest tests/test_learning.py -q`

Expected: pass.

## Task 2: Add Error Severity Scoring

**Files:**

- Create: `src/redaktsafe/learning.py`
- Test: `tests/test_learning.py`

**Step 1: Write failing tests**

Add tests for score ordering:

- missed direct identifier > eponym false positive,
- patient context > clean context,
- detector disagreement raises review priority,
- recurrence raises priority.

**Step 2: Run targeted tests**

Run: `python -m pytest tests/test_learning.py -q`

Expected: failure because scoring is missing.

**Step 3: Implement scoring**

Implement `score_correction(...)` and `route_for_score(...)` using transparent weighted components.

**Step 4: Run targeted tests**

Run: `python -m pytest tests/test_learning.py -q`

Expected: pass.

## Task 3: Add Encrypted Snippet Store

**Files:**

- Modify: `src/redaktsafe/learning.py`
- Test: `tests/test_learning.py`
- Modify: `.gitignore`

**Step 1: Write failing tests**

Add tests proving:

- stored snippet ciphertext does not contain the raw snippet,
- loading with the same passphrase restores the snippet,
- loading with the wrong passphrase fails,
- `.redaktsafe_learning/` is gitignored.

**Step 2: Run targeted tests**

Run: `python -m pytest tests/test_learning.py -q`

Expected: failure because encrypted storage is missing.

**Step 3: Implement store**

Implement `EncryptedSnippetStore` using:

- random 16-byte salt,
- random 16-byte nonce,
- `hashlib.pbkdf2_hmac("sha256", ...)`,
- HMAC-derived keystream,
- HMAC authentication tag.

**Step 4: Run targeted tests**

Run: `python -m pytest tests/test_learning.py -q`

Expected: pass.

## Task 4: Add Correction Ledger

**Files:**

- Modify: `src/redaktsafe/learning.py`
- Test: `tests/test_learning.py`

**Step 1: Write failing tests**

Add tests proving a correction append:

- writes JSONL without raw snippet text,
- stores only hashes and encrypted snippet reference,
- returns queue items sorted by score descending.

**Step 2: Run targeted tests**

Run: `python -m pytest tests/test_learning.py -q`

Expected: failure because ledger is missing.

**Step 3: Implement ledger**

Implement `LearningLedger.append_correction(...)`, `LearningLedger.list_corrections()`, and `LearningLedger.review_queue()`.

**Step 4: Run targeted tests**

Run: `python -m pytest tests/test_learning.py -q`

Expected: pass.

## Task 5: Add CLI Commands

**Files:**

- Modify: `src/redaktsafe/cli.py`
- Test: `tests/test_learning.py`
- Modify: `README.md`
- Modify: `PROGRESS.md`
- Modify: `DECISIONS.md`

**Step 1: Write failing tests**

Add tests for:

- `redaktsafe learning add-correction ...`,
- `redaktsafe learning queue ...`,
- no raw snippet appears in ledger JSONL.

**Step 2: Run targeted tests**

Run: `python -m pytest tests/test_learning.py -q`

Expected: failure because CLI commands do not exist.

**Step 3: Implement CLI**

Add `learning` subcommands:

- `add-correction`
- `queue`

Require explicit `--store`, `--passphrase`, and correction metadata. Keep learning disabled unless these commands are invoked.

**Step 4: Run verification**

Run:

```bash
python -m pytest tests/test_learning.py -q
python -m pytest -q
git diff --check
```

Expected: all pass.

## Task 6: Commit and Push

**Files:**

- Stage only learning-loop files and docs.
- Leave local benchmark CSV files untracked unless explicitly requested.

**Step 1: Inspect status**

Run: `git status --short --branch`

**Step 2: Commit**

Run:

```bash
git add .gitignore README.md DECISIONS.md PROGRESS.md docs/plans/2026-06-16-learning-loop-design.md docs/plans/2026-06-16-learning-loop.md src/redaktsafe/contracts.py src/redaktsafe/learning.py src/redaktsafe/cli.py tests/test_learning.py
git commit -m "Add local learning correction loop"
```

**Step 3: Push**

Run: `git push origin main`

