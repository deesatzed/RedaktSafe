from redaktsafe.adapters.protocols import UnavailableAdapter


def build_adapter() -> UnavailableAdapter:
    return UnavailableAdapter(
        adapter_id="mlx",
        reason="MLX/local model use is opt-in and not needed for default tests.",
    )

