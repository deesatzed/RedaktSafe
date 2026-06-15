from redaktsafe.adapters.protocols import UnavailableAdapter


def build_adapter() -> UnavailableAdapter:
    return UnavailableAdapter(
        adapter_id="openmed",
        reason="OpenMed is optional and no local model configuration was provided.",
    )

