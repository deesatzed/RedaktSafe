# 00 — Product Decision Memo

## Alien-goggles premise

An external observer would not identify the core problem as “humans need smaller LLMs.” It would identify a workflow failure:

- sensitive text is copied into tools before it is proven safe;
- AI outputs are reviewed without clear provenance;
- agents act on files and tools without a durable meaning layer;
- teams lack compact evidence showing what happened, what was removed, what was retained, and what remains risky.

Therefore the first product should not be another chatbot. It should be a **trust packet generator**.

## Why this option won

Three needs-based options were considered:

1. RedaktSafe Packet: local sensitive-text preflight and receipting.
2. Sentinel Evidence Workbench: governance replay and warranted-yet review.
3. Agent Guard / Pidgin Flight Recorder: safety wrapper for coding/tool agents.

Build Option 1 first because it:

- solves the most immediate repeated pain;
- is easiest to validate with users;
- has clear pass/fail safety metrics;
- becomes infrastructure for the other two options;
- makes small local models useful before any high-risk generation occurs.

## Product thesis

RedaktSafe creates a controlled transition from unsafe raw text to safe structured packets.

Raw text is not allowed to flow directly into downstream LLMs, RAG indexes, research exports, governance review, or agent tools. It must first pass through:

1. input profiling,
2. deterministic redaction baseline,
3. optional small-model PII/section classification,
4. safe reorganization,
5. residual-risk scoring,
6. receipt generation,
7. explicit user review.

## What makes this not a toy

A toy says:

> “Run a small model locally.”

This product says:

> “Before a sensitive document can move forward, prove it was cleaned, redacted, structured, and receipted.”

## Utility moat

The moat is not the model. The moat is the workflow contract:

- local-first execution;
- fail-closed safety gates;
- deterministic plus learned detection;
- no raw PHI in generated artifacts;
- structured packet outputs;
- receipts;
- measurable evaluation;
- pluggable expansion into governance and agent-safety workflows.

## Accuracy-for-size philosophy

Small models should not perform broad clinical reasoning. They should perform narrow high-frequency tasks:

- classify residual PII risk;
- label clinical sections;
- distinguish patient identifiers from clinical concepts;
- detect unsafe downstream intent;
- fill structured packet fields;
- propose receipt summaries.

The correct SOTA claim is not “best model.” It is:

> best local sensitive-text preflight accuracy per megabyte, millisecond, and user-review minute.

## Product wedge statement

For clinical AI builders, informaticists, and research teams who need to use messy sensitive text safely, RedaktSafe is a local preflight workbench that converts raw documents into redacted, structured, LLM-safe packets with receipts. Unlike ad hoc manual redaction or cloud-first AI workflows, RedaktSafe fails closed, runs locally by default, and produces auditable artifacts.
