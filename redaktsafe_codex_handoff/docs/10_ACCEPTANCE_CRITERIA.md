# 10 — Acceptance Criteria

## MVP v0.1 acceptance checklist

### Setup

- [ ] Clean clone installs with documented commands.
- [ ] Tests run without API keys.
- [ ] App runs without network access.
- [ ] Synthetic fixtures are included.

### CLI

- [ ] `redaktsafe doctor` runs.
- [ ] `redaktsafe packet input.txt --out outdir` creates artifacts.
- [ ] `redaktsafe text "..." --out outdir` creates artifacts.
- [ ] `redaktsafe eval` runs and writes report.
- [ ] Strict mode returns nonzero on high-risk/unsafe outputs.

### Pipeline

- [ ] Input profile created.
- [ ] Exact-line dedup applied.
- [ ] Deterministic detectors run.
- [ ] Spans merged deterministically.
- [ ] Redaction applied.
- [ ] Conservative section normalization applied after redaction.
- [ ] Residual risk lane assigned.
- [ ] Safe packet created.
- [ ] Receipt created.

### Artifacts

- [ ] `redacted.txt` exists.
- [ ] `safe_packet.json` validates.
- [ ] `redaction_report.json` validates.
- [ ] `receipt.json` validates.
- [ ] `receipt.md` exists.
- [ ] Raw input is absent from receipt.
- [ ] Artifact hashes are stable.

### Safety

- [ ] No cloud calls by default.
- [ ] No raw input logging.
- [ ] No compliance overclaims.
- [ ] High-risk fixtures fail closed.
- [ ] Path traversal tests pass.
- [ ] Model adapter failure does not mark output safe.

### API

- [ ] `/health` works.
- [ ] `/api/preflight` works.
- [ ] `/api/packet` writes scoped artifacts.
- [ ] Artifact route refuses path traversal.
- [ ] Input size limit enforced.

### UI

- [ ] Local UI starts.
- [ ] User can paste synthetic text.
- [ ] User can run local preflight.
- [ ] User sees risk lane and warnings.
- [ ] User can download artifacts.
- [ ] UI says not a compliance guarantee.

### Evaluation

- [ ] Eval report includes recall/precision by type.
- [ ] Unsafe-pass count is explicit.
- [ ] Latency is reported.
- [ ] Known limitations are documented.

## Do not mark complete if

- any artifact contains raw input unintentionally;
- any high-risk fixture is labeled safe without warning;
- running the app requires external API keys;
- UI or README claims compliance;
- model adapter errors are swallowed silently;
- output route can read arbitrary files;
- tests require real patient data.
