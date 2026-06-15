# RedaktSafe Standards

## Product Boundary

RedaktSafe is a local-first, privacy-supporting, deidentification-assistive trust packet workbench. It prepares synthetic, deidentified-style, clinical, research, and governance text for review by producing redacted artifacts, residual-risk information, and receipts.

It must not claim HIPAA compliance, guaranteed deidentification, external-sharing safety, clinical validation, production readiness, regulatory clearance, or patient-care decision support.

## Safety Rules

- Default operation makes no network calls and requires no API keys, credentials, GPU, model download, Docker, or external service.
- Fixtures, tests, docs, screenshots, and generated examples must not contain real PHI, secrets, credentials, private keys, or sensitive user data.
- Raw input may be read from a user-selected local file or pasted text, but it must not be copied into receipts, logs, default reports, or generated examples.
- Receipts may contain hashes, counts, detector metadata, risk lanes, artifact names, config hashes, and warnings, but not raw input or original span values.
- Redaction reports may contain offsets, replacement tokens, entity types, detector provenance, confidence, severity, and span hashes, but not raw original spans by default.
- Every packet and receipt must include residual-risk and review-required language.
- High-risk, uncertain, malformed, oversize, detector-failure, adapter-failure, or path-safety cases must fail closed.

## Engineering Rules

- Build in dependency order: deterministic CLI and artifacts first, evaluation second, API third, UI fourth, adapters last.
- Keep `redaktsafe_codex_handoff/` preserved as source documentation unless a committed decision explicitly supersedes it.
- Generated local run artifacts belong in gitignored locations such as `.redaktsafe_runs/` or explicit `/tmp/redaktsafe-*` paths.
- Deterministic detectors must remain mandatory and cannot be weakened or overridden by optional adapters.
- Optional adapters can add findings or metadata, but they cannot downgrade deterministic findings or mark uncertain output safe.
- Tests must not be weakened to make commands pass.

## Documentation Language

Use:

- local-first
- privacy-supporting
- deidentification-assistive
- review packet
- residual risk
- validate against your own data and policies

Avoid:

- HIPAA compliant
- guaranteed deidentified
- safe to share externally
- clinically validated
- production ready
- regulatory cleared

