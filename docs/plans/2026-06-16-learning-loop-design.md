# RedaktSafe Learning Loop Design

## Goal

Add a local learning mode that improves RedaktSafe through reviewed corrections, contextual pattern learning, and evidence-gated promotion without weakening the default offline deterministic baseline.

## Product Rule

Learning mode is opt-in. It may retain encrypted local snippets until learning is completed, but retained snippets must never be committed, copied into receipts, or used to make compliance or safety guarantees.

## Why This Exists

Raw PII detection errors do not have equal cost. A missed MRN, SSN, phone number, or date of birth is usually more dangerous than over-redacting an institution name. At the same time, over-redaction can destroy packet usefulness and can hide important clinical or research context. RedaktSafe needs to rank the expected harm of an additional classification error and use that ranking to decide when human review is required.

## Core Concepts

### Encrypted Snippet Store

Learning mode stores short local snippets around reviewed spans. Snippets are encrypted at rest and retained only until the configured learning or retention window expires. The initial implementation may use a password-derived local key because it keeps the feature self-contained and avoids adding a key-management service.

### Correction Ledger

Each correction records the reviewer decision, original detector decision, entity type, error type, context category, route, severity score, timestamps, hashes, and optional encrypted snippet reference.

Supported correction types:

- `false_negative`
- `false_positive`
- `wrong_entity_type`
- `contextual_allow`
- `contextual_redact`
- `uncertain`

### Context Pattern Library

The learning unit is context, not a bare token. RedaktSafe must never learn that a word such as `DeVries` is globally safe. It may learn that `DeVries syndrome` in disease context is usually not patient PII, while `Patient DeVries` near DOB/MRN/contact context is high risk.

Initial context categories:

- `direct_identifier`
- `patient_context`
- `medical_eponym`
- `institution`
- `building_or_unit`
- `research_lab`
- `clean_context`
- `unknown`

### Error Severity Score

Learning mode computes an error-severity score from:

- entity sensitivity
- error type cost
- context ambiguity
- downstream exposure
- model disagreement
- recurrence or novelty

The score determines review routing:

- `AUTO_REDACT`
- `REVIEW_REDACT`
- `REVIEW_ALLOW`
- `AUTO_ALLOW_WITH_TRACE`

The first implementation must bias toward review when the cost of being wrong is high.

## Nightly Audit

Every 24 hours, if learning activity exists, a future audit job should compare deterministic findings, optional model findings, reviewer corrections, and benchmark canaries. A larger local teacher model can propose mitigations, but it must run in audit/shadow mode first. It must not directly promote unsafe rules or model changes.

## Promotion Gates

A candidate learned change can become active only when:

- bundled tests pass,
- benchmark recall does not regress beyond the configured tolerance,
- unsafe-pass count does not increase,
- eponym, institution, building, lab, and patient-context canaries pass,
- the change is versioned and rollbackable,
- high-risk changes receive human approval.

## Fine-Tuning Position

Fine-tuning is feasible, but it should come after a reviewed correction corpus exists. The first target is rule/context learning and model-threshold calibration. Fine-tuning on unreviewed model guesses would amplify errors.

## Initial Safe Slice

The first implementation should add:

- correction contracts,
- error severity scoring,
- encrypted local snippet retention,
- a correction append command,
- a review queue command,
- tests proving snippets are encrypted and receipts remain raw-input-free.

