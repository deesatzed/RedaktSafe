# RedaktSafe PII Benchmark Guide

RedaktSafe supports optional benchmark adapters for standard PII/PHI-style datasets. These adapters are not part of the default offline test path: users must download or generate benchmark data themselves, review dataset terms, and keep benchmark outputs in local ignored paths such as `/tmp/redaktsafe-*` or `.redaktsafe_runs/`.

## Supported Benchmark Adapters

| Adapter | Source | Access | Expected local input |
| --- | --- | --- | --- |
| `nemotron_pii` | NVIDIA Nemotron-PII | Open synthetic Hugging Face dataset, CC BY 4.0 according to the dataset card | JSONL or JSON export with `text` and `spans` fields |
| `ai4privacy_300k` | AI4Privacy PII Masking 300k | Hugging Face dataset with dataset-specific license terms | JSONL or JSON export with `source_text` plus `privacy_mask` or `span_labels` |
| `kaggle_pii` | Learning Agency Lab PII Data Detection | Kaggle account and competition/data terms may be required | Kaggle `train.json` with `tokens` and `labels` |
| `presidio_synthetic` | Microsoft Presidio Research / generated samples | Local generated synthetic data | JSONL/JSON with `text` and `spans`, `entities`, or `annotations` |
| `n2c2_2014_deid` | n2c2/i2b2 2014 de-identification | Access-controlled clinical benchmark | Local converted JSONL/JSON with `text` and spans, or simple n2c2-style XML |

## Commands

List benchmark adapters:

```bash
python -m redaktsafe.cli benchmark list
```

Run a local benchmark export:

```bash
python -m redaktsafe.cli benchmark run \
  --source nemotron_pii \
  --input /path/to/nemotron_sample.jsonl \
  --out /tmp/redaktsafe-benchmark-nemotron \
  --limit 1000
```

Outputs:

- `benchmark_results.json`
- `benchmark_report.md`
- `converted/benchmark_cases.jsonl`
- `converted/texts/*.txt`
- `eval/eval_results.json`
- `eval/eval_report.md`
- per-case packet artifacts under `eval/runs/`

## Local Input Examples

Nemotron-style JSONL:

```json
{"uid":"n1","text":"I am Jason. My date of birth is 1987-05-22.","spans":[{"start":5,"end":10,"text":"Jason","label":"first_name"},{"start":32,"end":42,"text":"1987-05-22","label":"date_of_birth"}]}
```

AI4Privacy-style JSONL:

```json
{"id":"a1","source_text":"Email jane@example.com at 10:20am.","privacy_mask":[{"value":"jane@example.com","start":6,"end":22,"label":"EMAIL"}]}
```

Kaggle-style `train.json`:

```json
[{"document":7,"tokens":["My","email","is","jane@example.com"],"labels":["O","O","O","B-EMAIL"]}]
```

Presidio/generic JSONL:

```json
{"id":"p1","text":"Call 617-555-0142.","spans":[{"start":5,"end":17,"entity_type":"PHONE_NUMBER"}]}
```

## Safety Boundaries

- RedaktSafe does not download benchmark datasets automatically.
- Do not commit downloaded benchmark data or generated benchmark artifacts.
- For access-controlled clinical data, run only inside an approved local environment.
- Benchmark reports are performance evidence for the provided dataset only; they are not a compliance guarantee.
- External benchmark labels are normalized into RedaktSafe's current entity families: `ADDRESS`, `DATE`, `EMAIL`, `MRN`, `NAME`, `NPI`, `PHONE`, `SSN`, and `URL`.

## Current Limitations

- Kaggle token data is reconstructed by joining tokens with spaces unless a `full_text` field is present.
- Current metrics are entity-family-level metrics reused from the RedaktSafe eval runner, not strict character-offset span F1.
- Some benchmark datasets include entity classes outside the current deterministic baseline. Unsupported classes are ignored until RedaktSafe has detectors for them.
- n2c2/i2b2 official data access and format conversion remain user-managed.

