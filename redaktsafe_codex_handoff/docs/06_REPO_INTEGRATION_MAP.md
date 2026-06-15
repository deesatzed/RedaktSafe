# 06 — Repo Integration Map

## Primary implementation target

Build RedaktSafe as a new app/repo or isolated feature branch. Do not mutate existing repos until the MVP has stable contracts and tests.

## Existing repos and how they map

### redaktorg

Role: core redaction inspiration and likely package dependency.

Useful patterns:

- local-first document-intelligence pipeline;
- dedup before redaction;
- PHI/PII detection;
- learned clinical false-positive suppression;
- safety rule preventing aggressive trim before redaction.

Integration:

- Phase 6 adapter: `RedaktorgAdapter.detect_and_redact(text, config)`.
- If unavailable, use RedaktSafe deterministic baseline.

### Agent_Pidgeon

Role: semantic contracts, receipts, policy checks, and flight-recorder concepts.

Integration:

- Phase 6 adapter emits Pidgin-compatible receipt envelope.
- Future: use Pidgin to verify semantic pointer `clinical.phi.scrub` and packet contract.

### sentinel_arbiter

Role: future governance replay workbench.

Integration:

- Phase 8 export: `safe_packet -> sentinel draft episode`.
- RedaktSafe becomes the constructed/deidentified input preparation layer.

### loclM3

Role: local MLX model cockpit and UI/backend pattern.

Integration:

- Future: launch RedaktSafe packets into loclM3 as safe model context.
- Optional: reuse performance/model-registry concepts for small-model adapters.

### medical-autoXcon

Role: domain router pattern.

Integration:

- Future: classify safe packet into specialty/subspecialty before routing to downstream tool.

### tuhs-honest-broker

Role: research intake workflow.

Integration:

- Future: safe packet -> research request draft.
- Good vertical demo after RedaktSafe MVP.

### onco_snp_nutra

Role: conservative wellness-support discussion prioritization with provenance and uncertainty.

Integration:

- Future: RedaktSafe preflight before non-PHI context intake or evidence review artifacts.

### aXc-ace-forecaster

Role: operational forecasting and context compression pattern.

Integration:

- Future: RedaktSafe-style receipts for forecast narratives and data-quality notes.

### codebase-archaeology

Role: pattern discovery and multi-codebase integration.

Integration:

- Future: use Codebase Archaeology to identify reusable components and generate integration PRs.
- Agent Guard expansion track can consume risk labels from codebase archaeology.

## Avoided dependency trap

Do not make MVP require all repos. That creates integration drag and brittle setup.

Preferred sequence:

1. Build standalone RedaktSafe deterministic MVP.
2. Add optional adapters.
3. Prove each adapter with tests and graceful fallback.
4. Promote shared schemas only after real use.
