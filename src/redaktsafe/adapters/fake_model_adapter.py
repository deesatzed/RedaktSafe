from __future__ import annotations

from dataclasses import dataclass

from redaktsafe.adapters.protocols import AdapterFinding


@dataclass(frozen=True)
class FakeModelAdapter:
    entity_type: str
    needle: str
    adapter_id: str = "fake_model"
    available: bool = True

    def metadata(self) -> dict[str, str]:
        return {
            "adapter_id": self.adapter_id,
            "status": "available",
            "kind": "fake_local_model",
            "requires_download": "false",
        }

    def detect(self, text: str) -> list[AdapterFinding]:
        start = text.find(self.needle)
        if start < 0:
            return []
        return [
            AdapterFinding(
                adapter_id=self.adapter_id,
                entity_type=self.entity_type,
                start=start,
                end=start + len(self.needle),
                confidence=0.5,
                severity="medium",
            )
        ]

