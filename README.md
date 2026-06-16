# RedaktSafe Trust Packet Workbench

RedaktSafe is a local-first, privacy-supporting workbench for preparing synthetic or deidentified-style text for review. It creates redacted text, structured packet JSON, redaction reports, receipts, and validation summaries.

RedaktSafe is deidentification-assistive software. It does not replace human review, local policy review, legal review, security review, or clinical judgment. Generated artifacts may retain residual re-identification risk and should be reviewed before any downstream use.

## Current Status

This repository is being built from `redaktsafe_codex_handoff/`. The deterministic CLI and packet pipeline are the first implementation target. API, UI, and optional adapters come after the CLI and evaluation gates pass.

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
