# 09 — UI/UX Specification

## Design goal

The UI should make the safety boundary obvious. The user should always know:

- raw text is local;
- preflight is required before export;
- redacted output still needs review;
- receipts prove the path;
- the tool does not guarantee compliance.

## App layout

### Header

- Product name: RedaktSafe Trust Packet Workbench
- Status badges:
  - Local only
  - No cloud by default
  - Review required
  - Not a compliance guarantee

### Left panel: Input

- Paste textarea
- Upload `.txt` button
- Source label
- Clear button
- “Use synthetic demo” button
- Input size indicator

### Center panel: Preflight result

- Risk badge
- Entity counts
- Dedup ratio
- Detector summary
- Warnings
- “Why this risk lane?” explanation

### Right panel: Artifacts

- Download redacted text
- Download safe packet JSON
- Download redaction report JSON
- Download receipt JSON
- Download receipt Markdown

### Main review area

Tabs:

1. Redacted text
2. Entity summary
3. Sections
4. Receipt
5. Limitations

## Core interactions

1. User pastes text.
2. Button says `Run Local Preflight`.
3. UI displays progress.
4. Result shows risk lane.
5. If high risk, export requires acknowledgement.
6. User downloads artifacts.

## Required copy

Use plain language:

- “This packet is prepared for local review.”
- “This is not a guarantee that all identifiers are removed.”
- “Review before external sharing.”
- “No raw input was copied into the receipt.”

Avoid:

- “HIPAA compliant.”
- “Fully deidentified.”
- “Safe to upload anywhere.”

## Visual priorities

- Make risk lane prominent.
- Make limitations impossible to miss.
- Make downloads easy.
- Avoid dashboard clutter.
- Keep first-run path under 3 clicks.

## Empty states

Before input:

> Paste synthetic or deidentified-style text to create a local trust packet. Do not paste real PHI unless you are using this in an approved local environment.

No findings:

> No sensitive entities were detected by enabled detectors. This does not guarantee absence of identifiers. Review before downstream use.

High risk:

> This text may still contain sensitive information or the pipeline could not confidently classify it. Treat as not LLM-safe until manually reviewed.

## Accessibility

- Keyboard accessible controls.
- Color not sole signal for risk.
- Download buttons have clear labels.
- Text contrast sufficient.
- Tables have headers.
