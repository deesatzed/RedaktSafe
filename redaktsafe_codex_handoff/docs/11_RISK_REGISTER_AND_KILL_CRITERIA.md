# 11 — Risk Register and Kill Criteria

## Product risks

### Risk 1: Cool-tool trap

The app becomes another local AI demo rather than a workflow tool.

Mitigation:

- Keep packet generation and receipts as core.
- Validate with real workflow users.
- Measure time saved and artifact usefulness.

Kill signal:

- Users say “interesting” but cannot name a workflow where they would use it this week.

### Risk 2: False safety perception

Users may treat output as guaranteed deidentified.

Mitigation:

- Prominent residual-risk language.
- No compliance claims.
- Risk lanes and review requirements.

Kill signal:

- Users repeatedly interpret output as legally safe to share externally despite warnings.

### Risk 3: PHI miss

Detector misses sensitive identifiers.

Mitigation:

- Recall-first evaluation.
- Fail closed.
- Structured regex baseline.
- Human review.
- Hard adversarial fixtures.

Kill signal:

- Common structured identifiers are missed in bundled tests.

### Risk 4: Integration overreach

Trying to integrate all repos before the MVP works.

Mitigation:

- Standalone baseline first.
- Optional adapters later.
- Graceful fallback.

Kill signal:

- Clean clone cannot run without configuring multiple repos.

### Risk 5: UI overbuild

Frontend consumes effort before core safety is proven.

Mitigation:

- CLI first.
- UI after eval harness.

Kill signal:

- UI exists but pipeline metrics are missing.

### Risk 6: Model worship

Team optimizes model novelty instead of utility.

Mitigation:

- Accuracy-per-size scorecard.
- Deterministic fallback.
- Narrow task labels.

Kill signal:

- Model demos improve vibes but not recall, speed, or user task completion.

## Business validation kill criteria

Stop or pivot if after 15 target-user conversations:

- fewer than 5 have an active workflow involving sensitive text preparation;
- fewer than 3 would try a local packet tool on synthetic/deidentified data;
- no one values receipts/reports enough to change behavior;
- primary requested use is direct clinical advice rather than safe preparation.

## Technical kill criteria

Stop current approach if:

- deterministic baseline cannot reliably catch structured identifiers;
- generated artifacts cannot avoid raw input leakage;
- local latency is too slow for interactive use even on small files;
- path safety cannot be guaranteed in API mode.

## Pivot paths

If clinical text prep is too hard:

1. Pivot to research intake preflight.
2. Pivot to coding-agent sensitive-file guard.
3. Pivot to governance receipt generator for synthetic cases.

Do not pivot to a generic chatbot.
