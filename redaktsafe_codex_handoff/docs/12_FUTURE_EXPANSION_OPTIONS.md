# 12 — Future Expansion Options

## Expansion A — Sentinel Evidence Workbench

After RedaktSafe MVP, export safe packets into Sentinel episodes.

Flow:

```text
raw or deidentified-style text
  -> RedaktSafe packet
  -> reviewer-approved episode draft
  -> Sentinel node extraction
  -> deterministic warranted-yet graph
  -> committee packet + receipt
```

Need served:

- AI governance committees need evidence that outputs were reviewed responsibly.

Small-model roles:

- known facts extractor;
- missing-but-knowable extractor;
- source-trust classifier;
- next-best-input suggester.

## Expansion B — Agent Guard / Pidgin Flight Recorder

Use RedaktSafe as the text/file preflight layer for agent actions.

Flow:

```text
agent proposes tool/file/network action
  -> Agent Guard classifies risk
  -> RedaktSafe scans sensitive payloads
  -> Agent Pidgin resolves semantic contract
  -> allow / ask / block / escalate
  -> session receipt
```

Need served:

- developers want coding-agent productivity without blind trust.

Small-model roles:

- command-risk classifier;
- diff-risk classifier;
- semantic-drift scout;
- secret/PHI payload detector.

## Expansion C — Honest Broker Intake Packet

Use RedaktSafe to prepare research requests.

Flow:

```text
research email/intake text
  -> RedaktSafe preflight
  -> structured request draft
  -> missing fields
  -> risk lane
  -> approval packet
```

Need served:

- research governance teams need structured intakes and audit trails.

## Expansion D — Local Model Cockpit

Use loclM3 patterns to benchmark small models.

Flow:

```text
safe packet
  -> model registry
  -> run PII classifier / sectioner / normalizer
  -> compare latency/accuracy
  -> choose model for role
```

Need served:

- builders need to know which small model is actually useful for each task.

## Expansion E — Domain Router

Use medical-autoXcon patterns to route safe packets to specialties/tools.

Flow:

```text
safe packet
  -> domain/specialty classifier
  -> recommended downstream app
  -> allowed/disallowed action list
```

Need served:

- complex app portfolios need safe routing instead of one giant assistant.
