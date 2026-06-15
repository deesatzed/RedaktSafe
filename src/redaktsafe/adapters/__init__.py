from __future__ import annotations

from redaktsafe.adapters.protocols import OptionalAdapter, UnavailableAdapter

KNOWN_ADAPTERS = {
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

