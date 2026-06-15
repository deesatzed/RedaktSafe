from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def short_hash(value: str, length: int = 12) -> str:
    return sha256_text(value)[:length]


def stable_json_hash(value: Any) -> str:
    return sha256_text(json.dumps(value, sort_keys=True, separators=(",", ":"), default=str))


def read_text_file(path: Path) -> str:
    return path.read_text(encoding="utf-8")

