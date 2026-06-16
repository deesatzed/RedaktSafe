# RedaktSafe Trust Packet Workbench

RedaktSafe is a local-first, privacy-supporting workbench for preparing synthetic or deidentified-style text for review. It creates redacted text, structured packet JSON, redaction reports, receipts, and validation summaries.

RedaktSafe is deidentification-assistive software. It does not replace human review, local policy review, legal review, security review, or clinical judgment. Generated artifacts may retain residual re-identification risk and should be reviewed before any downstream use.

## Current Status

The local MVP is implemented from `redaktsafe_codex_handoff/`. It includes the deterministic CLI and packet pipeline, schema-backed artifacts, synthetic eval harness, optional benchmark adapters, local FastAPI service, static local UI, and an opt-in Hugging Face token-classification adapter. The default path remains offline and deterministic; model detection is optional and additive.

Opt-in learning mode now supports encrypted local snippet retention, reviewed correction capture, error-severity scoring, human-review queue routing, 24-hour-if-active audits, context canaries, shadow-mode mitigation candidates, promotion gates, and a fine-tuning export/dry-run path. It does not auto-promote high-risk changes or fine-tune models without enough reviewed corrections.

## Install

```bash
python -m pip install -e .
```

## Local Commands

```bash
python -m redaktsafe.cli doctor
python -m redaktsafe.cli schemas --out /tmp/redaktsafe-schemas
python -m redaktsafe.cli packet fixtures/synthetic/simple_identifiers.txt --out /tmp/redaktsafe-simple
python -m redaktsafe.cli packet fixtures/synthetic/high_risk_mixed_identifiers.txt --out /tmp/redaktsafe-risk --strict
python -m redaktsafe.cli eval --fixtures evals/cases.jsonl --out /tmp/redaktsafe-eval
python -m redaktsafe.cli benchmark list
python -m redaktsafe.cli benchmark compare \
  --source nemotron_pii \
  --input /path/to/nemotron_sample.jsonl \
  --out /tmp/redaktsafe-compare-nemotron-openmed \
  --hf-model-id OpenMed/OpenMed-PII-SuperClinical-Large-434M-v1 \
  --hf-min-score 0.20
python -m redaktsafe.cli serve --host 127.0.0.1 --port 8765
```

Optional Hugging Face model detection is available for packet and benchmark commands:

```bash
python -m pip install -e ".[models]"

python -m redaktsafe.cli text "Consult completed for Avery Stone." \
  --out /tmp/redaktsafe-model-smoke \
  --hf-model-id OpenMed/OpenMed-PII-SuperClinical-Large-434M-v1
```

Model access tokens can be provided through `HF_TOKEN`, `HUGGING_FACE_HUB_TOKEN`, or `HF_READ` in the environment or local `.env`.

Opt-in local learning correction capture:

```bash
python -m redaktsafe.cli learning add-correction \
  --store .redaktsafe_learning \
  --passphrase "local-passphrase" \
  --text "Patient DeVries, MRN E1234567." \
  --span-text "E1234567" \
  --entity-type MRN \
  --error-type false_negative \
  --context-category patient_context \
  --downstream-exposure external \
  --detector-disagreement

python -m redaktsafe.cli learning queue --store .redaktsafe_learning

python -m redaktsafe.cli learning corpus --store .redaktsafe_learning

python -m redaktsafe.cli learning audit \
  --store .redaktsafe_learning \
  --out /tmp/redaktsafe-learning-audit \
  --if-due \
  --interval-hours 24

python -m redaktsafe.cli learning canaries \
  --out /tmp/redaktsafe-learning-canaries

python -m redaktsafe.cli learning export-finetune \
  --store .redaktsafe_learning \
  --out /tmp/redaktsafe-finetune-export \
  --passphrase "local-passphrase" \
  --min-examples 100 \
  --dry-run
```

Learning context categories include patient context, medical eponym, provider-name ambiguity, institution, building/unit, research lab, direct identifier, clean context, and unknown.

After editable install, the console command is also available:

```bash
redaktsafe doctor
```

The local UI is served with the API at:

```text
http://127.0.0.1:8765/
```

## Safety Boundaries

- Default operation is local and does not call cloud services.
- No API key or model download is required for the default CLI.
- Receipts exclude raw input text and original redacted span values.
- Packets and receipts include residual-risk and review-required language.
- High-risk or uncertain outputs fail closed in strict mode.
- Synthetic fixtures are for testing only and are not real patient data.
- Optional adapters are off by default and are not required for tests, CLI, API, UI, or evaluation.
- Learning mode is off by default. When explicitly used, local snippets are encrypted at rest and correction ledgers store hashes and review metadata rather than plaintext snippets.
- Learning audits are advisory. Candidate mitigations remain in shadow mode with `promote=false` unless canary, benchmark, provenance, and human-review gates allow promotion.
- OpenMed-enabled benchmark comparison can improve recall, but model-backed promotion remains blocked when unsafe-pass or false-positive gates fail.

## Benchmarks

RedaktSafe includes optional benchmark adapters for NVIDIA Nemotron-PII, AI4Privacy PII Masking 300k, Kaggle/PIILO PII Data Detection, Presidio-generated samples, and n2c2/i2b2 2014 de-identification exports.

Benchmark datasets are not downloaded by default and are not required for tests. See `docs/BENCHMARKS.md`.

## Generated Artifacts

A packet run writes:

- `redacted.txt`
- `safe_packet.json`
- `redaction_report.json`
- `receipt.json`
- `receipt.md`
- `validation_summary.json`

Generated local run folders such as `.redaktsafe_runs/` are gitignored.
