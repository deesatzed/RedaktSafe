# Codex Phase 6–8 Adapter Prompt

Add optional adapter interfaces only after deterministic MVP, eval, API, and UI pass.

Adapters:

1. `redaktorg_adapter` — optional enhanced redaction pipeline.
2. `agent_pidgin_adapter` — receipt envelope and semantic contract export.
3. `sentinel_adapter` — safe packet to episode draft export.
4. `mlx_model_adapter` — optional local model detector interface.

Rules:

- All adapters are optional.
- App must work if adapters are missing.
- Adapter failure must fail closed or degrade safely.
- Adapter metadata must appear in receipts.
- No real model download in CI.
- Use fake model adapters for tests.

Acceptance:

- graceful fallback tests pass;
- receipt records adapter status;
- deterministic baseline remains default;
- docs explain how to enable adapters.
