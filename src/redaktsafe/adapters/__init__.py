from __future__ import annotations

from redaktsafe.adapters.protocols import OptionalAdapter, UnavailableAdapter

KNOWN_ADAPTERS = {
    "hf_token_classifier": "Hugging Face token-classification model is opt-in and requires local transformers runtime plus model access.",
    "openmed": "OpenMed adapter is opt-in and not bundled with the deterministic baseline.",
    "redaktorg": "redaktorg adapter is optional and not required for default operation.",
    "agent_pidgin": "Agent Pidgin export adapter is deferred until baseline artifacts pass.",
    "sentinel": "Sentinel export adapter is deferred until baseline artifacts pass.",
    "mlx": "Local model adapter is opt-in and requires explicit local model configuration.",
}


def load_optional_adapters(adapter_ids: list[str]) -> list[OptionalAdapter]:
    adapters: list[OptionalAdapter] = []
    for adapter_id in adapter_ids:
        reason = KNOWN_ADAPTERS.get(adapter_id, "Unknown optional adapter is not configured.")
        adapters.append(UnavailableAdapter(adapter_id=adapter_id, reason=reason))
    return adapters


def build_hf_token_classifier(settings: dict[str, str | float | int | bool]) -> OptionalAdapter:
    from redaktsafe.adapters.hf_token_classifier_adapter import HuggingFaceTokenClassifierAdapter

    model_id = str(settings.get("model_id") or "")
    if not model_id:
        return UnavailableAdapter(
            adapter_id="hf_token_classifier",
            reason="No Hugging Face model_id was provided.",
        )
    return HuggingFaceTokenClassifierAdapter(
        model_id=model_id,
        token=str(settings["token"]) if settings.get("token") else None,
        min_score=float(settings.get("min_score", 0.30)),
    )


ADAPTER_FACTORIES = {
    "hf_token_classifier": build_hf_token_classifier,
}

_ADAPTER_CACHE: dict[tuple[str, str, str], OptionalAdapter] = {}


def cached_adapter_factory(adapter_id: str, settings: dict[str, str | float | int | bool]) -> OptionalAdapter:
    key = (
        adapter_id,
        str(settings.get("model_id") or ""),
        str(settings.get("min_score", "")),
    )
    if key not in _ADAPTER_CACHE:
        factory = ADAPTER_FACTORIES[adapter_id]
        _ADAPTER_CACHE[key] = factory(settings)
    return _ADAPTER_CACHE[key]
