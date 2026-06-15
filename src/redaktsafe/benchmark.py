from __future__ import annotations

from redaktsafe.contracts import utc_now_iso


def benchmark_payload(benchmark_name: str, case_count: int, latency_ms: float) -> dict[str, object]:
    return {
        "benchmark_name": benchmark_name,
        "created_at": utc_now_iso(),
        "case_count": case_count,
        "latency_ms": latency_ms,
        "network_required": False,
        "model_download_required": False,
        "default_backend": "deterministic",
    }

