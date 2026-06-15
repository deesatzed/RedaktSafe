# 03 — Implementation Specification

## Tech stack

Backend/CLI:

- Python 3.12+
- Pydantic v2
- FastAPI
- Typer or argparse for CLI
- pytest
- ruff
- mypy optional but recommended
- uv for dependency management

Frontend:

- React + TypeScript + Vite
- No external analytics
- Local API only
- Plain downloadable artifacts

Optional model runtime:

- MLX / mlx-lm for Apple Silicon model adapters
- deterministic fallback must work without MLX

## Implementation priorities

1. Data contracts and schemas.
2. Deterministic baseline pipeline.
3. CLI.
4. Receipt and artifact writer.
5. Evaluation fixtures.
6. Local API.
7. Minimal UI.
8. Optional model adapters.
9. Future Sentinel/Pidgin adapters.

## Pipeline function

Implement a single orchestration entry point:

```python
def run_packet_pipeline(
    raw_text: str,
    config: PipelineConfig,
    source_name: str | None = None,
) -> PacketRunResult:
    ...
```

It should:

1. Create `InputProfile`.
2. Deduplicate exact lines.
3. Run deterministic detectors.
4. Run enabled model detectors.
5. Merge overlapping spans.
6. Apply redactions.
7. Section and normalize redacted text.
8. Compute residual risk.
9. Create `SafePacket`.
10. Create `Receipt`.
11. Return all artifacts in memory.

## Span merge rules

When spans overlap:

1. Prefer the most specific structured identifier type.
2. Never drop deterministic structured-ID findings.
3. Merge adjacent spans of the same entity type.
4. Preserve detector provenance list.
5. Use highest risk severity among contributors.

Example:

```json
{
  "start": 18,
  "end": 27,
  "text_hash": "...",
  "entity_type": "MRN",
  "replacement": "[REDACTED_MRN]",
  "detectors": ["regex_mrn", "model_phi_token_classifier"],
  "confidence": 1.0,
  "severity": "high"
}
```

## Redaction replacement rules

- Replacements must be deterministic by type unless user enables stable pseudonyms.
- Preserve readability.
- Do not expose original value in reports.
- Reports may include original span hashes but not raw originals.
- Optional debug mode may include raw spans only in local workspace and must be disabled by default.

## Input profile fields

Include:

- character count;
- line count;
- duplicate line count;
- duplicate line ratio;
- possible EHR-scaffold indicators;
- detector count;
- maximum entity severity;
- config hash;
- source name;
- created timestamp.

## Safe packet fields

Minimum:

- `packet_id`
- `schema_version`
- `created_at`
- `source_hash`
- `redacted_text_hash`
- `redacted_text`
- `sections`
- `detected_entity_summary`
- `residual_risk`
- `limitations`
- `allowed_downstream_uses`
- `disallowed_downstream_uses`
- `receipt_id`

## Receipt fields

Minimum:

- `receipt_id`
- `schema_version`
- `created_at`
- `pipeline_version`
- `config_hash`
- `source_hash`
- `artifacts`
- `detectors_used`
- `model_adapters_used`
- `risk_lane`
- `counts_by_entity_type`
- `dedup_summary`
- `policy_findings`
- `output_hashes`
- `warnings`
- `no_raw_input_copied: true`

## Workspace policy

Default workspace:

```text
.redaktsafe_runs/
```

Run directory:

```text
.redaktsafe_runs/{timestamp}_{short_hash}/
```

Generated artifacts must be local and gitignored.

## Error handling

Fail closed.

If detector or model adapter fails:

- record error in `policy_findings`;
- set risk lane to `PIPELINE_ERROR_FAIL_CLOSED` or `NEEDS_MANUAL_REVIEW`;
- do not mark as LLM-safe;
- return actionable error to user.

## Security details

- No network calls in default pipeline.
- Disable remote model calls by default.
- API must only serve generated artifacts from scoped run directories.
- Prevent path traversal in artifact routes.
- Reject binary files for MVP.
- Limit input size with configurable max.
- Scrub logs; never log raw input by default.

## Performance details

- Deterministic detectors should run in linear time for normal text.
- Cache compiled regexes.
- Avoid copying raw text into multiple artifact files.
- Model adapters should run only after dedup when possible.
- Keep benchmark output in CI.

## Frontend requirements

Single-page local UI:

1. Paste/upload panel.
2. Run Preflight button.
3. Risk badge.
4. Redacted text review.
5. Entity summary table.
6. Dedup/cleanup summary.
7. Limitations panel.
8. Download buttons for packet/report/receipt.

No login. No cloud accounts. No telemetry.
