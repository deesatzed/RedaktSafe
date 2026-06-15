# 05 — Small Model Strategy

## Principle

Small models are not used because they are fashionable. They are used because preflight needs to be always-on, cheap, private, and fast.

## Role taxonomy

### Role 1 — PII/PHI span detector

Purpose:

- identify sensitive entities missed by regex;
- improve context-dependent detection;
- support token-level review.

Size target:

- 33M to 100M parameters if possible;
- quantized for local inference;
- high recall priority.

### Role 2 — Clinical section classifier

Purpose:

- preserve meaningful note sections;
- prevent cleanup from deleting clinical anchors;
- support safe packet structure.

Size target:

- 100M to 250M parameters;
- or rules + embeddings baseline if accuracy is adequate.

### Role 3 — Residual-risk classifier

Purpose:

- classify whether output still looks unsafe;
- detect suspicious remaining identifiers;
- recommend fail-closed lane when uncertain.

Size target:

- 100M to 250M parameters.

### Role 4 — Packet normalizer

Purpose:

- convert redacted text into structured sections;
- summarize limitations;
- draft reviewer-facing summary.

Size target:

- 250M to 1B parameters.

## What small models must not do

- diagnose;
- prescribe;
- decide disposition;
- claim compliance;
- override deterministic detectors;
- downgrade known PHI;
- send raw text externally;
- silently mark uncertain output as safe.

## Accuracy-for-size scorecard

Every model adapter must report:

- model id;
- revision or local path;
- quantization;
- disk size;
- memory usage if measured;
- latency on standard fixture set;
- recall and precision by entity type;
- unsafe-pass count;
- abstention rate;
- residual-risk calibration;
- known failure modes.

## Evaluation datasets

MVP starts with synthetic fixtures only:

1. simple structured identifiers;
2. duplicated EHR-like scaffold;
3. clinical false-positive traps;
4. physician-name vs patient-name ambiguity;
5. date ambiguity;
6. MRN-like lab values;
7. OCR/noisy punctuation;
8. unsafe cloud-export intent text;
9. notes with no PHI;
10. notes with hidden PHI in footer/header style lines.

Later datasets:

- governance-approved deidentified corpora;
- manually labeled local cases;
- public deidentification benchmarks if licensing allows;
- user opt-in correction logs with no raw PHI persisted unless explicitly configured.

## Distillation plan

1. Use deterministic detectors to create weak labels.
2. Use larger models as label proposal engines only on synthetic/deidentified text.
3. Human-review gold labels.
4. Train small task-specific model.
5. Quantize.
6. Evaluate against gold and adversarial fixtures.
7. Add failures back to training/eval loop.

## Deployment plan

Default pipeline:

```text
regex + rules only
```

Optional enhanced pipeline:

```text
regex + rules + local token classifier + residual-risk model
```

Never require model download for base app. If a model is missing, fail gracefully and continue with deterministic baseline.

## SOTA claim discipline

Only claim SOTA after benchmarking. Use narrow claims:

- “best observed recall per MB on our synthetic PHI stress suite,” not “best redactor.”
- “fastest local packet generation on M-series Mac in our benchmark,” not “fastest in the world.”
- “zero unsafe-pass on bundled fixtures,” not “HIPAA compliant.”
