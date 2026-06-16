from __future__ import annotations

import re
from pathlib import Path
from uuid import uuid4

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from redaktsafe.artifacts import write_artifacts
from redaktsafe.contracts import LearningContextCategory, LearningErrorType, PipelineConfig
from redaktsafe.learning import LearningLedger
from redaktsafe.pipeline import REQUIRED_ARTIFACTS, run_packet_pipeline

ALLOWED_ARTIFACTS = set(REQUIRED_ARTIFACTS)
ALLOWED_FRONTEND_ASSETS = {"app.js", "styles.css"}
RUN_ID_PATTERN = re.compile(r"^[A-Za-z0-9_-]+$")


class TextRequest(BaseModel):
    text: str = Field(min_length=1)
    source_name: str | None = None


class LearningCorrectionRequest(BaseModel):
    passphrase: str = Field(min_length=1)
    text: str = Field(min_length=1)
    span_text: str = Field(min_length=1)
    entity_type: str = Field(min_length=1)
    error_type: LearningErrorType
    context_category: LearningContextCategory
    downstream_exposure: str = "local"
    detector_disagreement: bool = False
    reviewer_id: str | None = None
    note: str | None = None


def create_app(
    run_root: str | Path = ".redaktsafe_runs",
    max_input_chars: int = 200_000,
    learning_root: str | Path = ".redaktsafe_learning",
) -> FastAPI:
    app = FastAPI(title="RedaktSafe Local API", version="0.1.0")
    root = Path(run_root)
    learning_root_path = Path(learning_root)
    frontend_root = Path(__file__).resolve().parents[3] / "frontend"

    @app.get("/")
    def index():
        path = frontend_root / "index.html"
        if not path.exists():
            raise HTTPException(status_code=404, detail="UI not found")
        return FileResponse(path)

    @app.get("/frontend/{asset_name}")
    def frontend_asset(asset_name: str):
        if asset_name not in ALLOWED_FRONTEND_ASSETS:
            raise HTTPException(status_code=404, detail="Unknown UI asset")
        path = (frontend_root / asset_name).resolve()
        try:
            path.relative_to(frontend_root.resolve())
        except ValueError:
            raise HTTPException(status_code=404, detail="Unknown UI asset") from None
        if not path.is_file():
            raise HTTPException(status_code=404, detail="Unknown UI asset")
        return FileResponse(path)

    @app.get("/health")
    def health() -> dict[str, object]:
        return {
            "status": "healthy",
            "service": "redaktsafe",
            "network_required": False,
            "credentials_required": False,
        }

    @app.post("/api/preflight")
    def preflight(request: TextRequest) -> dict[str, object]:
        _enforce_size(request.text, max_input_chars)
        result = run_packet_pipeline(
            request.text,
            PipelineConfig(max_input_chars=max_input_chars),
            source_name=request.source_name or "api-preflight",
        )
        return {
            "risk_lane": result.safe_packet.residual_risk.lane.value,
            "reasons": result.safe_packet.residual_risk.reasons,
            "warnings": result.receipt.warnings,
            "counts_by_entity_type": result.redaction_report.counts_by_entity_type,
            "redacted_text": result.redacted_text,
            "detected_spans": [span.model_dump(mode="json") for span in result.redaction_report.detected_spans],
            "limitations": result.safe_packet.limitations,
        }

    @app.post("/api/packet")
    def packet(request: TextRequest) -> dict[str, object]:
        _enforce_size(request.text, max_input_chars)
        run_id = f"run_{uuid4().hex[:16]}"
        run_dir = root / run_id
        result = run_packet_pipeline(
            request.text,
            PipelineConfig(max_input_chars=max_input_chars),
            source_name=request.source_name or "api-packet",
        )
        result = write_artifacts(result, run_dir)
        return {
            "run_id": run_id,
            "risk_lane": result.safe_packet.residual_risk.lane.value,
            "counts_by_entity_type": result.redaction_report.counts_by_entity_type,
            "artifact_urls": {
                name: f"/api/artifacts/{run_id}/{name}"
                for name in sorted(ALLOWED_ARTIFACTS)
            },
            "warnings": result.receipt.warnings,
        }

    @app.get("/api/artifacts/{run_id}/{artifact_name}")
    def artifact(run_id: str, artifact_name: str):
        if not RUN_ID_PATTERN.fullmatch(run_id):
            raise HTTPException(status_code=404, detail="Unknown run")
        if artifact_name not in ALLOWED_ARTIFACTS:
            raise HTTPException(status_code=404, detail="Unknown artifact")

        run_dir = (root / run_id).resolve()
        candidate = (run_dir / artifact_name)
        try:
            resolved = candidate.resolve(strict=True)
            resolved.relative_to(run_dir)
        except (FileNotFoundError, ValueError):
            raise HTTPException(status_code=404, detail="Unknown artifact") from None

        if not resolved.is_file():
            raise HTTPException(status_code=404, detail="Unknown artifact")
        return FileResponse(resolved)

    @app.post("/api/learning/corrections")
    def add_learning_correction(request: LearningCorrectionRequest) -> dict[str, object]:
        _enforce_size(request.text, max_input_chars)
        ledger = LearningLedger(learning_root_path, passphrase=request.passphrase)
        correction = ledger.append_correction(
            text=request.text,
            span_text=request.span_text,
            entity_type=request.entity_type,
            error_type=request.error_type,
            context_category=request.context_category,
            downstream_exposure=request.downstream_exposure,
            detector_disagreement=request.detector_disagreement,
            reviewer_id=request.reviewer_id,
            note=request.note,
        )
        return correction.model_dump(mode="json")

    @app.get("/api/learning/queue")
    def learning_queue() -> list[dict[str, object]]:
        ledger = LearningLedger(learning_root_path)
        return [item.model_dump(mode="json") for item in ledger.review_queue()]

    return app


def _enforce_size(text: str, max_input_chars: int) -> None:
    if len(text) > max_input_chars:
        raise HTTPException(status_code=413, detail="Input exceeds configured size limit")


app = create_app()
