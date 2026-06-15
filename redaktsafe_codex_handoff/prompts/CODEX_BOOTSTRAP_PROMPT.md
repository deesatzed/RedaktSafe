# Codex Bootstrap Prompt

You are Codex building the RedaktSafe Trust Packet Workbench from this handoff package.

Read these files first:

1. README_CODEX_HANDOFF.md
2. docs/00_PRODUCT_DECISION_MEMO.md
3. docs/01_PRODUCT_REQUIREMENTS.md
4. docs/02_ARCHITECTURE_AND_DATA_FLOW.md
5. docs/03_IMPLEMENTATION_SPEC.md
6. docs/04_BUILD_PLAN_AND_MILESTONES.md
7. docs/07_TESTING_AND_EVAL_PLAN.md
8. docs/08_SECURITY_PRIVACY_GOVERNANCE.md
9. tasks/codex_task_queue.yml

Your goal is to build the MVP in dependency order.

Non-negotiables:

- Do not use real PHI.
- Do not claim HIPAA compliance or clinical validation.
- Do not add cloud calls by default.
- Do not log raw input.
- Do not place raw input in receipts.
- Fail closed when uncertain.
- Deterministic baseline must work without MLX or external models.
- Tests must run in clean clone without credentials.

Start with Phase 0 through Phase 2:

1. Bootstrap package.
2. Implement contracts.
3. Implement deterministic detectors.
4. Implement dedup/profile.
5. Implement span merge and redaction.
6. Implement packet pipeline.
7. Implement CLI artifact writer.
8. Add tests and synthetic fixtures.

After each phase:

- run tests;
- summarize what changed;
- identify residual risks;
- do not proceed to UI/model work until the current phase passes.

Definition of done for your first autonomous pass:

`redaktsafe packet fixtures/synthetic/high_risk_mixed_identifiers.txt --out /tmp/redaktsafe-demo --strict`

creates artifacts and marks high-risk output as needing review or not LLM-safe.
