from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
from pathlib import Path
from uuid import uuid4

from redaktsafe.contracts import (
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
