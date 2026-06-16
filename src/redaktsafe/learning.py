from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any
from uuid import uuid4

from redaktsafe.contracts import (
    LearningAuditCandidate,
    LearningAuditReport,
    LearningContextCategory,
    LearningCorrection,
    LearningErrorType,
    LearningQueueItem,
    LearningScore,
    ReviewRoute,
    utc_now_iso,
)
from redaktsafe.util import sha256_text

KDF_ITERATIONS = 200_000

ENTITY_SENSITIVITY = {
    "SSN": 35,
    "MRN": 35,
    "NPI": 30,
    "ID": 30,
    "EMAIL": 28,
    "PHONE": 28,
    "ADDRESS": 28,
    "DATE": 22,
    "NAME": 20,
    "USERNAME": 18,
    "URL": 14,
}

ERROR_COST = {
    LearningErrorType.FALSE_NEGATIVE: 30,
    LearningErrorType.CONTEXTUAL_REDACT: 24,
    LearningErrorType.WRONG_ENTITY_TYPE: 18,
    LearningErrorType.UNCERTAIN: 16,
    LearningErrorType.FALSE_POSITIVE: 10,
    LearningErrorType.CONTEXTUAL_ALLOW: 2,
}

CONTEXT_COST = {
    LearningContextCategory.DIRECT_IDENTIFIER: 24,
    LearningContextCategory.PATIENT_CONTEXT: 22,
    LearningContextCategory.UNKNOWN: 18,
    LearningContextCategory.PROVIDER_NAME: 14,
    LearningContextCategory.BUILDING_OR_UNIT: 12,
    LearningContextCategory.RESEARCH_LAB: 10,
    LearningContextCategory.INSTITUTION: 8,
    LearningContextCategory.MEDICAL_EPONYM: 6,
    LearningContextCategory.CLEAN_CONTEXT: 2,
}


def score_correction(
    *,
    entity_type: str,
    error_type: LearningErrorType | str,
    context_category: LearningContextCategory | str,
    downstream_exposure: str,
    detector_disagreement: bool = False,
    recurrence_count: int = 0,
) -> LearningScore:
    error = LearningErrorType(error_type)
    context = LearningContextCategory(context_category)
    normalized_entity = entity_type.upper()
    normalized_exposure = downstream_exposure.lower()

    score = ENTITY_SENSITIVITY.get(normalized_entity, 16)
    score += ERROR_COST[error]
    score += CONTEXT_COST[context]

    if normalized_exposure in {"external", "cloud", "export", "public"}:
        score += 18
    elif normalized_exposure in {"team", "shared"}:
        score += 10
    else:
        score += 3

    if detector_disagreement:
        score += 12
    if recurrence_count:
        score += min(10, recurrence_count * 3)

    if error == LearningErrorType.CONTEXTUAL_ALLOW and context in {
        LearningContextCategory.MEDICAL_EPONYM,
        LearningContextCategory.INSTITUTION,
        LearningContextCategory.RESEARCH_LAB,
        LearningContextCategory.CLEAN_CONTEXT,
    }:
        score -= 35
    if error == LearningErrorType.FALSE_POSITIVE and context == LearningContextCategory.MEDICAL_EPONYM:
        score -= 15

    bounded = max(0, min(100, score))
    route = _route_for_score(
        bounded,
        error_type=error,
        context_category=context,
        entity_type=normalized_entity,
    )
    return LearningScore(
        score=bounded,
        route=route,
        reasons=[
            f"entity_sensitivity={ENTITY_SENSITIVITY.get(normalized_entity, 16)}",
            f"error_type={error.value}",
            f"context={context.value}",
            f"downstream_exposure={normalized_exposure}",
            f"detector_disagreement={detector_disagreement}",
            f"recurrence_count={recurrence_count}",
        ],
    )


def _route_for_score(
    score: int,
    *,
    error_type: LearningErrorType,
    context_category: LearningContextCategory,
    entity_type: str,
) -> ReviewRoute:
    if error_type in {LearningErrorType.FALSE_NEGATIVE, LearningErrorType.CONTEXTUAL_REDACT}:
        return ReviewRoute.REVIEW_REDACT
    if error_type in {LearningErrorType.FALSE_POSITIVE, LearningErrorType.CONTEXTUAL_ALLOW}:
        if score < 25 and context_category in {
            LearningContextCategory.MEDICAL_EPONYM,
            LearningContextCategory.INSTITUTION,
            LearningContextCategory.RESEARCH_LAB,
            LearningContextCategory.CLEAN_CONTEXT,
        }:
            return ReviewRoute.AUTO_ALLOW_WITH_TRACE
        return ReviewRoute.REVIEW_ALLOW
    if score >= 70:
        return ReviewRoute.REVIEW_REDACT
    return ReviewRoute.REVIEW_ALLOW


class EncryptedSnippetStore:
    def __init__(self, root: str | Path) -> None:
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)

    def store(self, snippet: str, *, passphrase: str) -> str:
        snippet_id = f"snippet_{uuid4().hex[:16]}"
        salt = os.urandom(16)
        nonce = os.urandom(16)
        plaintext = snippet.encode("utf-8")
        key = _derive_key(passphrase, salt)
        ciphertext = _xor_bytes(plaintext, _keystream(key, nonce, len(plaintext)))
        tag = hmac.new(key, nonce + ciphertext, hashlib.sha256).digest()
        payload = {
            "version": 1,
            "kdf": "pbkdf2_hmac_sha256",
            "iterations": KDF_ITERATIONS,
            "salt": _b64(salt),
            "nonce": _b64(nonce),
            "ciphertext": _b64(ciphertext),
            "tag": _b64(tag),
        }
        (self.root / f"{snippet_id}.snippet").write_text(json.dumps(payload, sort_keys=True) + "\n", encoding="utf-8")
        return snippet_id

    def load(self, snippet_id: str, *, passphrase: str) -> str:
        path = self.root / f"{snippet_id}.snippet"
        payload = json.loads(path.read_text(encoding="utf-8"))
        salt = _unb64(payload["salt"])
        nonce = _unb64(payload["nonce"])
        ciphertext = _unb64(payload["ciphertext"])
        expected_tag = _unb64(payload["tag"])
        key = _derive_key(passphrase, salt)
        actual_tag = hmac.new(key, nonce + ciphertext, hashlib.sha256).digest()
        if not hmac.compare_digest(actual_tag, expected_tag):
            raise ValueError("snippet authentication failed")
        plaintext = _xor_bytes(ciphertext, _keystream(key, nonce, len(ciphertext)))
        return plaintext.decode("utf-8")


class LearningLedger:
    def __init__(self, root: str | Path, *, passphrase: str | None = None) -> None:
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)
        self.passphrase = passphrase
        self.snippets = EncryptedSnippetStore(self.root / "snippets")
        self.ledger_path = self.root / "corrections.jsonl"
        self.audit_state_path = self.root / "audit_state.json"

    def append_correction(
        self,
        *,
        text: str,
        span_text: str,
        entity_type: str,
        error_type: LearningErrorType | str,
        context_category: LearningContextCategory | str,
        downstream_exposure: str,
        detector_disagreement: bool = False,
        reviewer_id: str | None = None,
        note: str | None = None,
    ) -> LearningCorrection:
        if not self.passphrase:
            raise ValueError("a passphrase is required to retain encrypted snippets")
        recurrence_count = self._recurrence_count(entity_type, error_type, context_category)
        score = score_correction(
            entity_type=entity_type,
            error_type=error_type,
            context_category=context_category,
            downstream_exposure=downstream_exposure,
            detector_disagreement=detector_disagreement,
            recurrence_count=recurrence_count,
        )
        snippet_ref = self.snippets.store(text, passphrase=self.passphrase)
        correction = LearningCorrection(
            correction_id=f"corr_{uuid4().hex[:16]}",
            created_at=utc_now_iso(),
            reviewer_id=reviewer_id,
            entity_type=entity_type.upper(),
            error_type=LearningErrorType(error_type),
            context_category=LearningContextCategory(context_category),
            downstream_exposure=downstream_exposure,
            detector_disagreement=detector_disagreement,
            recurrence_count=recurrence_count,
            severity_score=score.score,
            route=score.route,
            source_hash=sha256_text(text),
            span_hash=sha256_text(span_text),
            snippet_ref=snippet_ref,
            note_hash=sha256_text(note) if note else None,
        )
        with self.ledger_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(correction.model_dump(mode="json"), sort_keys=True) + "\n")
        return correction

    def list_corrections(self) -> list[LearningCorrection]:
        if not self.ledger_path.exists():
            return []
        corrections = []
        for line in self.ledger_path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                corrections.append(LearningCorrection(**json.loads(line)))
        return corrections

    def review_queue(self) -> list[LearningQueueItem]:
        items = [
            LearningQueueItem(
                correction_id=correction.correction_id,
                severity_score=correction.severity_score,
                route=correction.route,
                entity_type=correction.entity_type,
                error_type=correction.error_type,
                context_category=correction.context_category,
                downstream_exposure=correction.downstream_exposure,
                detector_disagreement=correction.detector_disagreement,
                recurrence_count=correction.recurrence_count,
                created_at=correction.created_at,
            )
            for correction in self.list_corrections()
        ]
        return sorted(items, key=lambda item: (-item.severity_score, item.created_at))

    def corpus_summary(self) -> dict[str, Any]:
        corrections = self.list_corrections()
        context_counts = {context.value: 0 for context in LearningContextCategory}
        entity_counts: dict[str, int] = {}
        error_counts = {error.value: 0 for error in LearningErrorType}
        for correction in corrections:
            context_counts[correction.context_category.value] += 1
            entity_counts[correction.entity_type] = entity_counts.get(correction.entity_type, 0) + 1
            error_counts[correction.error_type.value] += 1
        return {
            "correction_count": len(corrections),
            "context_counts": context_counts,
            "entity_counts": dict(sorted(entity_counts.items())),
            "error_counts": error_counts,
        }

    def audit_state(self) -> dict[str, Any]:
        if not self.audit_state_path.exists():
            return {}
        return json.loads(self.audit_state_path.read_text(encoding="utf-8"))

    def write_audit_state(self, report: LearningAuditReport) -> None:
        state = {
            "last_audit_at": report.created_at,
            "last_correction_count": report.correction_count,
            "last_audit_id": report.audit_id,
        }
        self.audit_state_path.write_text(json.dumps(state, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    def _recurrence_count(
        self,
        entity_type: str,
        error_type: LearningErrorType | str,
        context_category: LearningContextCategory | str,
    ) -> int:
        normalized_entity = entity_type.upper()
        normalized_error = LearningErrorType(error_type)
        normalized_context = LearningContextCategory(context_category)
        return sum(
            1
            for correction in self.list_corrections()
            if correction.entity_type == normalized_entity
            and correction.error_type == normalized_error
            and correction.context_category == normalized_context
        )


def context_canary_cases() -> list[dict[str, str]]:
    return [
        {
            "case_id": "eponym_devries_syndrome",
            "text": "The note discusses DeVries syndrome in the differential.",
            "context_category": LearningContextCategory.MEDICAL_EPONYM.value,
            "expected_route": ReviewRoute.REVIEW_ALLOW.value,
        },
        {
            "case_id": "patient_devries_identifier",
            "text": "Patient DeVries, DOB 1970-01-01, MRN E1234567, called today.",
            "context_category": LearningContextCategory.PATIENT_CONTEXT.value,
            "expected_route": ReviewRoute.REVIEW_REDACT.value,
        },
        {
            "case_id": "provider_devries_name",
            "text": "Dr. DeVries reviewed the synthetic teaching case.",
            "context_category": LearningContextCategory.PROVIDER_NAME.value,
            "expected_route": ReviewRoute.REVIEW_ALLOW.value,
        },
        {
            "case_id": "institution_johns_hopkins",
            "text": "The protocol cites Johns Hopkins Hospital as a reference site.",
            "context_category": LearningContextCategory.INSTITUTION.value,
            "expected_route": ReviewRoute.REVIEW_ALLOW.value,
        },
        {
            "case_id": "building_east_tower",
            "text": "Specimens were delivered to East Tower before noon.",
            "context_category": LearningContextCategory.BUILDING_OR_UNIT.value,
            "expected_route": ReviewRoute.REVIEW_ALLOW.value,
        },
        {
            "case_id": "research_lab_devries",
            "text": "The assay was repeated by DeVries Lab for quality review.",
            "context_category": LearningContextCategory.RESEARCH_LAB.value,
            "expected_route": ReviewRoute.REVIEW_ALLOW.value,
        },
    ]


def run_learning_audit(
    *,
    store: str | Path,
    out_dir: str | Path,
    if_due: bool = False,
    interval_hours: int = 24,
    teacher_adapter: Any | None = None,
) -> LearningAuditReport:
    ledger = LearningLedger(store)
    corrections = ledger.list_corrections()
    state = ledger.audit_state()
    new_corrections = _new_corrections_since_state(corrections, state)

    if if_due:
        skip_reason = _audit_skip_reason(state, corrections, new_corrections, interval_hours)
        if skip_reason:
            report = _audit_report(
                interval_hours=interval_hours,
                corrections=corrections,
                new_corrections=[],
                skipped=True,
                skip_reason=skip_reason,
                teacher_adapter=teacher_adapter,
            )
            _write_audit_artifacts(report, out_dir)
            return report

    report = _audit_report(
        interval_hours=interval_hours,
        corrections=corrections,
        new_corrections=new_corrections,
        skipped=False,
        skip_reason=None,
        teacher_adapter=teacher_adapter,
    )
    _write_audit_artifacts(report, out_dir)
    ledger.write_audit_state(report)
    return report


def export_finetuning_dataset(
    *,
    store: str | Path,
    out_dir: str | Path,
    passphrase: str,
    min_examples: int = 100,
    dry_run: bool = False,
) -> dict[str, Any]:
    ledger = LearningLedger(store, passphrase=passphrase)
    corrections = ledger.list_corrections()
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    examples = []
    for correction in corrections:
        if not correction.snippet_ref:
            continue
        snippet = ledger.snippets.load(correction.snippet_ref, passphrase=passphrase)
        examples.append(
            {
                "correction_id": correction.correction_id,
                "text": snippet,
                "entity_type": correction.entity_type,
                "error_type": correction.error_type.value,
                "context_category": correction.context_category.value,
                "route": correction.route.value,
            }
        )

    ready = len(examples) >= min_examples
    result = {
        "ready": ready,
        "dry_run": dry_run,
        "example_count": len(examples),
        "minimum_required": min_examples,
        "reason": "ready" if ready else "insufficient_reviewed_corrections",
        "dataset_path": str(out / "finetune_examples.jsonl") if ready and not dry_run else None,
        "manifest_path": str(out / "finetune_manifest.json"),
    }
    (out / "finetune_manifest.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if ready and not dry_run:
        with (out / "finetune_examples.jsonl").open("w", encoding="utf-8") as handle:
            for example in examples:
                handle.write(json.dumps(example, sort_keys=True) + "\n")
    return result


def run_context_canary_eval(out_dir: str | Path) -> dict[str, int | float | bool | str]:
    results = _run_context_canaries()
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    payload = {
        **results,
        "cases": context_canary_cases(),
    }
    (out / "learning_canary_results.json").write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (out / "learning_canary_report.md").write_text(_canary_markdown(payload), encoding="utf-8")
    return results


def _new_corrections_since_state(corrections: list[LearningCorrection], state: dict[str, Any]) -> list[LearningCorrection]:
    last_count = int(state.get("last_correction_count", 0) or 0)
    return corrections[last_count:]


def _audit_skip_reason(
    state: dict[str, Any],
    corrections: list[LearningCorrection],
    new_corrections: list[LearningCorrection],
    interval_hours: int,
) -> str | None:
    if not corrections:
        return "no_activity"
    if not new_corrections:
        return "no_new_activity"
    last_audit_at = state.get("last_audit_at")
    if last_audit_at:
        last_dt = datetime.fromisoformat(str(last_audit_at))
        if datetime.now(last_dt.tzinfo) - last_dt < timedelta(hours=interval_hours):
            return "not_due"
    return None


def _audit_report(
    *,
    interval_hours: int,
    corrections: list[LearningCorrection],
    new_corrections: list[LearningCorrection],
    skipped: bool,
    skip_reason: str | None,
    teacher_adapter: Any | None = None,
) -> LearningAuditReport:
    canary_results = _run_context_canaries()
    benchmark_gate_results = _benchmark_gate_results(corrections, canary_results)
    candidates = [] if skipped else _candidate_mitigations(new_corrections)
    teacher_summary = _teacher_model_summary(teacher_adapter, new_corrections)
    promote = bool(
        candidates
        and benchmark_gate_results["promotion_allowed"]
        and all(candidate.promote for candidate in candidates)
    )
    return LearningAuditReport(
        audit_id=f"audit_{uuid4().hex[:16]}",
        created_at=utc_now_iso(),
        skipped=skipped,
        skip_reason=skip_reason,
        interval_hours=interval_hours,
        correction_count=len(corrections),
        new_activity_count=len(new_corrections),
        failure_summary=_failure_summary(new_corrections),
        detector_disagreement_summary=_detector_disagreement_summary(new_corrections),
        teacher_model_summary=teacher_summary,
        candidate_mitigations=candidates,
        canary_results=canary_results,
        benchmark_gate_results=benchmark_gate_results,
        promotion_recommendation={
            "promote": promote,
            "candidate_count": len(candidates),
            "reason": "all_gates_passed" if promote else "human_review_or_gate_required",
        },
    )


class UnavailableTeacherAuditAdapter:
    def __init__(self, model_id: str) -> None:
        self.model_id = model_id

    def metadata(self) -> dict[str, str]:
        return {
            "adapter_id": "teacher_model",
            "status": "unavailable",
            "model_id": self.model_id,
            "reason": "Teacher-model inference is optional and not configured for default tests.",
        }

    def review(self, _corrections: list[LearningCorrection]) -> list[dict[str, str]]:
        return []


def _teacher_model_summary(teacher_adapter: Any | None, corrections: list[LearningCorrection]) -> dict[str, int | float | bool | str]:
    if teacher_adapter is None:
        return {"adapter_id": "none", "status": "not_configured", "suggestion_count": 0}
    metadata = dict(teacher_adapter.metadata())
    suggestions = teacher_adapter.review(corrections)
    return {
        **metadata,
        "suggestion_count": len(suggestions),
    }


def _candidate_mitigations(corrections: list[LearningCorrection]) -> list[LearningAuditCandidate]:
    candidates = []
    for correction in sorted(corrections, key=lambda item: item.severity_score, reverse=True):
        candidates.append(
            LearningAuditCandidate(
                candidate_id=f"cand_{sha256_text(correction.correction_id)[:12]}",
                version="candidate-0.1.0",
                source_correction_ids=[correction.correction_id],
                context_category=correction.context_category,
                severity_score=correction.severity_score,
                mitigation_type=_mitigation_type(correction),
                description=_mitigation_description(correction),
                shadow_mode=True,
                promote=False,
                gate_results={
                    "requires_human_review": correction.route in {ReviewRoute.REVIEW_REDACT, ReviewRoute.REVIEW_ALLOW},
                    "canary_required": True,
                    "unsafe_pass_increase_allowed": False,
                },
                rollback_ref=f"rollback_{sha256_text(correction.correction_id)[:12]}",
            )
        )
    return candidates


def _mitigation_type(correction: LearningCorrection) -> str:
    if correction.error_type in {LearningErrorType.FALSE_NEGATIVE, LearningErrorType.CONTEXTUAL_REDACT}:
        return "contextual_redact_candidate"
    if correction.error_type in {LearningErrorType.FALSE_POSITIVE, LearningErrorType.CONTEXTUAL_ALLOW}:
        return "contextual_allow_candidate"
    return "review_route_candidate"


def _mitigation_description(correction: LearningCorrection) -> str:
    return (
        f"Shadow candidate for {correction.entity_type} "
        f"{correction.error_type.value} in {correction.context_category.value} context."
    )


def _failure_summary(corrections: list[LearningCorrection]) -> dict[str, int]:
    summary = {error_type.value: 0 for error_type in LearningErrorType}
    for correction in corrections:
        summary[correction.error_type.value] += 1
    return summary


def _detector_disagreement_summary(corrections: list[LearningCorrection]) -> dict[str, int]:
    with_disagreement = sum(1 for correction in corrections if correction.detector_disagreement)
    return {
        "with_disagreement": with_disagreement,
        "without_disagreement": len(corrections) - with_disagreement,
    }


def _run_context_canaries() -> dict[str, int | float | bool | str]:
    cases = context_canary_cases()
    unsafe_pass_count = 0
    for case in cases:
        score = score_correction(
            entity_type="MRN" if case["context_category"] == LearningContextCategory.PATIENT_CONTEXT.value else "NAME",
            error_type=LearningErrorType.FALSE_NEGATIVE
            if case["context_category"] == LearningContextCategory.PATIENT_CONTEXT.value
            else LearningErrorType.FALSE_POSITIVE,
            context_category=case["context_category"],
            downstream_exposure="external" if case["context_category"] == LearningContextCategory.PATIENT_CONTEXT.value else "local",
            detector_disagreement=case["context_category"] == LearningContextCategory.PATIENT_CONTEXT.value,
        )
        if case["expected_route"] == ReviewRoute.REVIEW_REDACT.value and score.route != ReviewRoute.REVIEW_REDACT:
            unsafe_pass_count += 1
    return {
        "case_count": len(cases),
        "unsafe_pass_count": unsafe_pass_count,
        "passed": unsafe_pass_count == 0,
    }


def _benchmark_gate_results(
    corrections: list[LearningCorrection],
    canary_results: dict[str, int | float | bool | str],
) -> dict[str, int | float | bool | str]:
    high_risk_review_count = sum(
        1
        for correction in corrections
        if correction.error_type == LearningErrorType.FALSE_NEGATIVE and correction.route == ReviewRoute.REVIEW_REDACT
    )
    return {
        "promotion_allowed": False,
        "reason": "shadow_mode_requires_human_promotion",
        "canary_passed": bool(canary_results.get("passed")),
        "high_risk_review_count": high_risk_review_count,
        "unsafe_pass_count": int(canary_results.get("unsafe_pass_count", 0)),
    }


def _write_audit_artifacts(report: LearningAuditReport, out_dir: str | Path) -> None:
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    payload = report.model_dump(mode="json")
    (out / "audit_report.json").write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (out / "audit_report.md").write_text(_audit_markdown(payload), encoding="utf-8")


def _audit_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# RedaktSafe Learning Audit",
        "",
        f"- audit id: `{payload['audit_id']}`",
        f"- skipped: `{payload['skipped']}`",
        f"- skip reason: `{payload.get('skip_reason')}`",
        f"- correction count: {payload['correction_count']}",
        f"- new activity count: {payload['new_activity_count']}",
        f"- promote: `{payload['promotion_recommendation']['promote']}`",
        "",
        "This audit is local, opt-in, and advisory. Candidate mitigations remain in shadow mode until gates and review allow promotion.",
        "",
        "## Candidate Mitigations",
    ]
    for candidate in payload["candidate_mitigations"]:
        lines.append(
            f"- {candidate['candidate_id']}: {candidate['mitigation_type']}, "
            f"score={candidate['severity_score']}, promote={candidate['promote']}"
        )
    return "\n".join(lines) + "\n"


def _canary_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# RedaktSafe Learning Canary Report",
        "",
        f"- case count: {payload['case_count']}",
        f"- unsafe-pass count: {payload['unsafe_pass_count']}",
        f"- passed: `{payload['passed']}`",
        "",
        "Canaries cover contextual PII ambiguity only. They are not proof that all identifiers will be detected.",
        "",
        "## Cases",
    ]
    for case in payload["cases"]:
        lines.append(f"- {case['case_id']}: {case['context_category']}")
    return "\n".join(lines) + "\n"


def _derive_key(passphrase: str, salt: bytes) -> bytes:
    return hashlib.pbkdf2_hmac("sha256", passphrase.encode("utf-8"), salt, KDF_ITERATIONS, dklen=32)


def _keystream(key: bytes, nonce: bytes, length: int) -> bytes:
    chunks: list[bytes] = []
    counter = 0
    while sum(len(chunk) for chunk in chunks) < length:
        chunks.append(hmac.new(key, nonce + counter.to_bytes(8, "big"), hashlib.sha256).digest())
        counter += 1
    return b"".join(chunks)[:length]


def _xor_bytes(left: bytes, right: bytes) -> bytes:
    return bytes(left_byte ^ right_byte for left_byte, right_byte in zip(left, right, strict=True))


def _b64(value: bytes) -> str:
    return base64.b64encode(value).decode("ascii")


def _unb64(value: str) -> bytes:
    return base64.b64decode(value.encode("ascii"))
