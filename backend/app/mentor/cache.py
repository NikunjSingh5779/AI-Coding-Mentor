"""Hint cache keyed by code, diagnostics, level, prompt version and model."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field


def compute_prompt_hash(
    code: str,
    diagnostics: list[dict],
    level: int,
    prompt_version: str,
    model: str,
) -> str:
    """Stable hash over everything that determines a hint's content."""
    payload = json.dumps(
        {
            "code": code,
            "diagnostics": sorted(
                (d.get("fingerprint", "") for d in diagnostics),
            ),
            "level": level,
            "prompt_version": prompt_version,
            "model": model,
        },
        sort_keys=True,
    )
    return hashlib.sha256(payload.encode()).hexdigest()


@dataclass
class HintCache:
    """In-memory LRU-ish hint cache (bounded)."""

    max_entries: int = 256
    _store: dict[str, str] = field(default_factory=dict)

    def get(self, key: str) -> str | None:
        return self._store.get(key)

    def put(self, key: str, hint_text: str) -> None:
        if len(self._store) >= self.max_entries:
            # Drop the oldest entry (dicts keep insertion order).
            self._store.pop(next(iter(self._store)))
        self._store[key] = hint_text

    def clear(self) -> None:
        self._store.clear()
