# RedaktSafe Task Queue

Source: `redaktsafe_codex_handoff/tasks/codex_task_queue.yml`.

## Completed

- P0-001: Bootstrap Python package.
- P1-001: Define Pydantic contracts.
- P1-002: Implement deterministic regex detectors.
- P1-003: Implement dedup and input profile.
- P1-004: Implement span merge and redaction.
- P2-001: Implement packet pipeline.
- P2-002: Implement artifact writer and CLI packet command.
- P3-001: Implement evaluation harness.
- P4-001: Implement FastAPI local service.
- P5-001: Implement minimal local UI.
- P6-001: Add optional adapter interfaces.
- P7-001: Add fake model adapter tests and benchmark hooks.
- P8-001: Add optional external PII benchmark adapters.
- P9-001: Add opt-in real Hugging Face token-classification model detector.
- P10-001: Add opt-in encrypted local learning correction ledger and severity-ranked review queue.
- P11-001: Add 24-hour-if-active learning audit, context canaries, shadow-mode promotion gates, and fine-tuning export/dry-run.
- P12-001: Add benchmark backend comparison, reviewer correction API/UI, correction corpus summary including provider-name ambiguity, optional teacher-adapter injection, and expanded entity taxonomy.

## Active

None.

## Pending

None.

## Deferred Until Baseline Passes

- Broad adapter integrations beyond Hugging Face token classification and teacher-audit injection.
- Real teacher-model inference beyond unavailable/fake audit adapter metadata.
- Actual model fine-tuning after enough reviewed corrections exist.
- Sentinel and Agent Pidgin export bridges.
- Production deployment, auth, database integration, live EHR integration, or cloud workflows.
