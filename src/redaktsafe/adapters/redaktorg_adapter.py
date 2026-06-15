from redaktsafe.adapters.protocols import UnavailableAdapter


def build_adapter() -> UnavailableAdapter:
    return UnavailableAdapter(
        adapter_id="redaktorg",
        reason="redaktorg is optional and not bundled into the default deterministic baseline.",
    )

