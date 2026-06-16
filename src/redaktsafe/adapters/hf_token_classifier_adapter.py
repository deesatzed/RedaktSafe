from __future__ import annotations

import os
from pathlib import Path
from collections.abc import Callable
from typing import Any

from redaktsafe.adapters.protocols import AdapterFinding
from redaktsafe.contracts import Severity
from redaktsafe.util import sha256_text

ENTITY_MAP = {
    "address": "ADDRESS",
    "city": "ADDRESS",
    "country": "ADDRESS",
    "date": "DATE",
    "date_of_birth": "DATE",
    "dob": "DATE",
    "email": "EMAIL",
    "email_address": "EMAIL",
    "first_name": "NAME",
    "givenname": "NAME",
    "last_name": "NAME",
    "location": "ADDRESS",
    "medical_record": "MRN",
    "medical_record_number": "MRN",
    "mrn": "MRN",
    "idcard": "ID",
    "id_card": "ID",
    "identity_card": "ID",
    "identity_card_number": "ID",
    "passport_number": "ID",
    "national_id": "ID",
    "national_id_number": "ID",
    "name": "NAME",
    "patient": "NAME",
    "person": "NAME",
    "phone": "PHONE",
    "phone_number": "PHONE",
    "ssn": "SSN",
    "street_address": "ADDRESS",
    "url": "URL",
    "username": "USERNAME",
}


class HuggingFaceTokenClassifierAdapter:
    adapter_id = "hf_token_classifier"
    available = True

    def __init__(
        self,
        model_id: str,
        token: str | None = None,
        min_score: float = 0.30,
        pipeline_factory: Callable[[str, str | None], Any] | None = None,
    ) -> None:
        self.model_id = model_id
        self.token = token or _huggingface_token()
        self.min_score = min_score
        self._pipeline_factory = pipeline_factory or _build_pipeline
        self._pipeline = None

    def metadata(self) -> dict[str, str]:
        return {
            "adapter_id": self.adapter_id,
            "status": "available",
            "kind": "huggingface_token_classification",
            "model_id": self.model_id,
            "min_score": str(self.min_score),
            "token_source": "configured" if self.token else "hf_cache_or_public",
        }

    def detect(self, text: str) -> list[AdapterFinding]:
        runner = self._get_pipeline()
        try:
            raw_entities = runner(text, aggregation_strategy="simple")
        except TypeError:
            raw_entities = runner(text)
        findings: list[AdapterFinding] = []
        for raw in raw_entities:
            entity_type = _normalize_entity(str(raw.get("entity_group") or raw.get("entity") or raw.get("label") or ""))
            start = raw.get("start")
            end = raw.get("end")
            score = float(raw.get("score", raw.get("confidence", 0.0)))
            if entity_type is None or start is None or end is None or score < self.min_score:
                continue
            start_i = int(start)
            end_i = int(end)
            if end_i <= start_i:
                continue
            findings.append(
                AdapterFinding(
                    adapter_id=self.adapter_id,
                    entity_type=entity_type,
                    start=start_i,
                    end=end_i,
                    confidence=score,
                    severity=_severity_for(entity_type).value,
                    text_hash=sha256_text(text[start_i:end_i]),
                )
            )
        return findings

    def _get_pipeline(self):
        if self._pipeline is None:
            self._pipeline = self._pipeline_factory(self.model_id, self.token)
        return self._pipeline


def _build_pipeline(model_id: str, token: str | None):
    return DirectTokenClassificationRunner(model_id=model_id, token=token)


def _huggingface_token() -> str | None:
    for key in ("HF_TOKEN", "HUGGING_FACE_HUB_TOKEN", "HF_READ"):
        value = os.environ.get(key)
        if value:
            return value
    env_path = Path.cwd() / ".env"
    if env_path.exists():
        for line in env_path.read_text(encoding="utf-8").splitlines():
            stripped = line.strip()
            if not stripped or stripped.startswith("#") or "=" not in stripped:
                continue
            key, value = stripped.split("=", 1)
            if key.strip() in {"HF_TOKEN", "HUGGING_FACE_HUB_TOKEN", "HF_READ"}:
                return value.strip().strip('"').strip("'")
    return None


class DirectTokenClassificationRunner:
    def __init__(self, model_id: str, token: str | None = None) -> None:
        import torch
        from transformers import AutoConfig, AutoModelForTokenClassification, AutoTokenizer, DebertaV2ForTokenClassification

        kwargs: dict[str, Any] = {}
        if token:
            os.environ.setdefault("HF_TOKEN", token)
            kwargs["token"] = token
        self._torch = torch
        self.config = AutoConfig.from_pretrained(model_id, **kwargs)
        self.tokenizer = AutoTokenizer.from_pretrained(model_id, **kwargs)
        if self.config.model_type == "deberta-v2":
            self.model = DebertaV2ForTokenClassification.from_pretrained(model_id, **kwargs)
        else:
            # The generic AutoModel path supports standard token classifiers, but some
            # current environments have a transformers/kernels auto-mapping bug. Keep
            # it after the known direct loader path.
            self.model = AutoModelForTokenClassification.from_pretrained(model_id, **kwargs)
        self.model.eval()

    def __call__(self, text: str) -> list[dict[str, Any]]:
        encoded = self.tokenizer(
            text,
            return_offsets_mapping=True,
            return_tensors="pt",
            truncation=True,
        )
        offsets = encoded.pop("offset_mapping")[0].tolist()
        with self._torch.no_grad():
            logits = self.model(**encoded).logits[0]
            probabilities = self._torch.softmax(logits, dim=-1)
            scores, label_ids = probabilities.max(dim=-1)

        entities: list[dict[str, Any]] = []
        current: dict[str, Any] | None = None
        for offset, label_id, score in zip(offsets, label_ids.tolist(), scores.tolist(), strict=False):
            start, end = int(offset[0]), int(offset[1])
            if start == end:
                continue
            raw_label = str(self.model.config.id2label.get(int(label_id), "O"))
            if raw_label == "O":
                if current:
                    entities.append(current)
                    current = None
                continue

            entity = raw_label.replace("B-", "").replace("I-", "")
            if (
                current
                and current["entity_group"] == entity
                and start <= int(current["end"]) + 1
            ):
                current["end"] = end
                current["word"] = text[int(current["start"]):end]
                current["score"] = min(float(current["score"]), float(score))
            else:
                if current:
                    entities.append(current)
                current = {
                    "entity_group": entity,
                    "word": text[start:end],
                    "start": start,
                    "end": end,
                    "score": float(score),
                }
        if current:
            entities.append(current)
        return entities


def _normalize_entity(label: str) -> str | None:
    cleaned = label.strip()
    if not cleaned:
        return None
    cleaned = cleaned.replace("B-", "").replace("I-", "")
    key = cleaned.lower().replace(" ", "_").replace("-", "_")
    if key.startswith("pii_"):
        key = key[4:]
    if key in ENTITY_MAP:
        return ENTITY_MAP[key]
    upper = key.upper()
    if upper in {"ADDRESS", "DATE", "EMAIL", "ID", "MRN", "NAME", "NPI", "PHONE", "SSN", "URL", "USERNAME"}:
        return upper
    return None


def _severity_for(entity_type: str) -> Severity:
    if entity_type in {"SSN", "MRN", "NPI", "ID"}:
        return Severity.CRITICAL
    if entity_type in {"NAME", "EMAIL", "PHONE", "ADDRESS", "USERNAME"}:
        return Severity.HIGH
    return Severity.MEDIUM
