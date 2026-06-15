# CODEX.md — Autonomous Build Instructions

Build RedaktSafe Trust Packet Workbench.

Start with deterministic CLI MVP. Do not build UI, model adapters, or cloud features until CLI, artifacts, receipts, and eval pass.

Core command to support first:

```bash
redaktsafe packet fixtures/synthetic/high_risk_mixed_identifiers.txt --out /tmp/redaktsafe-demo --strict
```

Required outputs:

- redacted.txt
- safe_packet.json
- redaction_report.json
- receipt.json
- receipt.md
- validation_summary.json

Never:

- use real PHI;
- claim HIPAA compliance;
- log raw input;
- copy raw input into receipts;
- call remote APIs by default;
- mark uncertain output as safe.

Build order:

1. P0-001 bootstrap package.
2. P1-001 contracts.
3. P1-002 detectors.
4. P1-003 dedup/profile.
5. P1-004 span merge/redaction.
6. P2-001 pipeline.
7. P2-002 CLI/artifacts.
8. P3-001 eval harness.
9. P4-001 API.
10. P5-001 UI.
11. P6+ optional adapters.

Use `tasks/codex_task_queue.yml` as the task source of truth.
