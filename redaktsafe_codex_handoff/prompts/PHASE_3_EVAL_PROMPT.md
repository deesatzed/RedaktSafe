# Codex Phase 3 Evaluation Prompt

Add the evaluation harness.

Requirements:

- `redaktsafe eval --fixtures evals/cases.jsonl --out eval_results/`
- JSONL fixture format with expected entities.
- Metrics: recall, precision, false positives, unsafe-pass count, latency.
- Markdown report.
- CI-safe: no external data, no API keys, no model downloads.

The eval must fail if high-risk fixtures are incorrectly marked safe.

Add at least 10 synthetic fixtures covering:

1. simple identifiers;
2. duplicate EHR scaffold;
3. clinical false positives;
4. doctor vs patient names;
5. dates and phones;
6. clean no-PHI note;
7. hidden footer identifier;
8. unsafe export intent;
9. OCR-like noise;
10. research intake text.
