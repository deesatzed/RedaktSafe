from redaktsafe.adapters.protocols import UnavailableAdapter


def build_adapter() -> UnavailableAdapter:
    return UnavailableAdapter(
        adapter_id="agent_pidgin",
        reason="Agent Pidgin export is a deferred optional integration.",
    )

