# Codex Phase 4–5 API/UI Prompt

Build the local API and minimal UI.

Backend:

- FastAPI app.
- `GET /health`.
- `POST /api/preflight`.
- `POST /api/packet`.
- `GET /api/artifacts/{run_id}/{artifact_name}` scoped to generated artifacts only.

Security:

- block path traversal;
- enforce input size;
- do not log raw input;
- no network calls;
- no arbitrary local file read.

Frontend:

- React + Vite + TypeScript.
- Paste text or upload `.txt`.
- Run Local Preflight.
- Show risk lane, warnings, entity summary, redacted text, limitations.
- Download artifacts.
- Prominent local-only / review-required / not-compliance-guarantee language.

Do not add auth, analytics, cloud model calls, or broad chat features.
