from redaktsafe.adapters.protocols import UnavailableAdapter


def build_adapter() -> UnavailableAdapter:
    return UnavailableAdapter(
        adapter_id="sentinel",
        reason="Sentinel export is a deferred optional integration.",
    )

