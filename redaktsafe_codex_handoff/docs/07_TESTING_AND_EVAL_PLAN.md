# 07 — Testing and Evaluation Plan

## Testing philosophy

This app lives or dies by safety and usefulness. Tests must prove not only that code runs, but that the app fails closed under ambiguous or high-risk input.

## Test layers

### Unit tests

- regex detectors;
- span merge;
- redaction application;
- dedup profile;
- risk lane calculation;
- receipt creation;
- schema validation;
- path traversal prevention;
- no raw input in receipts.

### Pipeline tests

- file input to artifact output;
- pasted text to in-memory report;
- strict mode fail-closed;
- model adapter failure fallback;
- redaktorg adapter missing fallback;
- oversized input behavior.

### API tests

- `/health` returns status;
- `/api/preflight` returns report;
- `/api/packet` writes scoped artifacts;
- artifact route refuses path traversal;
- raw text is not logged.

### UI smoke tests

If feasible:

- app loads;
- paste text;
- click preflight;
- risk badge appears;
- redacted output appears;
- download links resolve.

## Evaluation cases

Create `evals/cases.jsonl` with fields:

```json
{
  "case_id": "simple_identifiers_001",
  "text": "Patient Jane Doe, MRN E4567890, phone 617-555-0142.",
  "expected_entities": [
    {"entity_type": "NAME", "text": "Jane Doe"},
    {"entity_type": "MRN", "text": "E4567890"},
    {"entity_type": "PHONE", "text": "617-555-0142"}
  ],
  "expected_min_risk_lane": "NEEDS_MANUAL_REVIEW"
}
```

Do not include real PHI.

## Metrics

- recall by entity type;
- precision by entity type;
- unsafe-pass count;
- false-positive count;
- latency by case;
- artifact completeness;
- receipt completeness;
- no-raw-input violations;
- fail-closed count.

## Gates

MVP release gates:

- unsafe-pass count = 0 on high-risk fixtures;
- receipt completeness = 100%;
- no raw input appears in receipt artifacts;
- path traversal tests pass;
- no network call required;
- README/UI contains no compliance overclaim;
- all tests pass in clean clone.

## Regression fixtures

Must include:

1. `simple_identifiers.txt`
2. `duplicate_ehr_scaffold.txt`
3. `clinical_false_positive_drug_names.txt`
4. `doctor_vs_patient_name.txt`
5. `date_and_phone_ambiguity.txt`
6. `no_phi_clean_note.txt`
7. `hidden_footer_identifier.txt`
8. `unsafe_cloud_export_request.txt`
9. `ocr_like_noise.txt`
10. `mixed_research_intake.txt`

## Manual evaluation script

Create `docs/MANUAL_EVAL_SCRIPT.md` later with:

- setup instructions;
- sample run;
- expected output review;
- questions for user feedback;
- task timing form.

## User utility metrics

During validation sessions, measure:

- time to create safe packet manually;
- time using RedaktSafe;
- number of edits user makes;
- user confidence before/after;
- whether user would use this in next real workflow;
- what artifact is most valuable: redacted text, report, receipt, or structured packet.
