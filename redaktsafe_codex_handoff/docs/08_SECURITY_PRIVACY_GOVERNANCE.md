# 08 — Security, Privacy, and Governance

## Product stance

RedaktSafe is a local-first software tool that supports privacy-conscious workflows. It is not a compliance guarantee, not a HIPAA certification, not clinically validated, and not intended for direct patient-care recommendations.

## Required language

Use:

- “local-first”
- “privacy-supporting”
- “deidentification-assistive”
- “review packet”
- “residual risk”
- “validate against your own data and policies”

Do not use:

- “HIPAA compliant”
- “guaranteed deidentified”
- “safe to share externally”
- “clinically validated”
- “production ready”
- “regulatory cleared”

## Raw input handling

Default behavior:

- raw input exists only in memory during processing;
- raw input may be read from user-selected file;
- raw input is not copied into receipts;
- raw input is not logged;
- raw input is not transmitted externally;
- raw input is not persisted unless user explicitly requests debug mode.

## Artifact handling

Generated artifacts may contain redacted text and summaries. They must still be treated as sensitive until reviewed.

Artifacts must include warnings:

- “This output may retain residual re-identification risk.”
- “Review before external sharing.”
- “This tool is not a compliance guarantee.”

## Network policy

Default: no network calls.

Optional model downloads or external model calls require explicit user configuration and must be reflected in receipts.

Never silently call remote APIs.

## Secret handling

- Do not require API keys for MVP.
- If future adapters use API keys, read from environment only.
- Never log secrets.
- Add tests for secret-like string redaction in logs.

## Path safety

- Output paths must be explicit.
- Artifact download route must only serve files in the run directory.
- Reject `..`, absolute paths, symlink escapes, and unrecognized artifact names.

## Governance packet principles

Every generated packet should answer:

1. What source artifact was processed? Hash only, not raw content.
2. What detectors and models were used?
3. What was removed or transformed?
4. What risks remain?
5. What downstream uses are allowed or disallowed?
6. What receipt proves this?

## Clinical safety boundaries

The app can:

- prepare text;
- structure text;
- highlight missing metadata;
- produce redaction and review reports;
- export safe packets.

The app must not:

- diagnose;
- recommend treatment;
- provide patient-specific dosing;
- determine disposition;
- replace clinical review;
- rank patient-care actions.

## Logging rules

Default logs may include:

- run ID;
- artifact names;
- counts;
- risk lane;
- detector IDs;
- timings.

Default logs must not include:

- raw input;
- original redacted spans;
- secrets;
- user file contents;
- raw patient-like identifiers.
