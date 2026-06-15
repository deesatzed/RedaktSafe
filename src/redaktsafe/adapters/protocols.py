from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class AdapterFinding:
    adapter_id: str
    entity_type: str
    start: int
    end: int
    confidence: float
    severity: str


class OptionalAdapter(Protocol):
    adapter_id: str
    available: bool

    def metadata(self) -> dict[str, str]:
        ...

    def detect(self, text: str) -> list[AdapterFinding]:
        ...


@dataclass(frozen=True)
class UnavailableAdapter:
    adapter_id: str
    reason: str
    available: bool = False

    def metadata(self) -> dict[str, str]:
        return {
            "adapter_id": self.adapter_id,
            "status": "unavailable",
            "reason": self.reason,
        }

    def detect(self, text: str) -> list[AdapterFinding]:
        return []

