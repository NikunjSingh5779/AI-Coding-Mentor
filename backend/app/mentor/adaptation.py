from __future__ import annotations

from collections.abc import Iterable

from app.schemas.diagnostic import Diagnostic

def recommend_hint_level(
    diagnostics: Iterable[Diagnostic],
    *,
    prior_hint_count: int = 0,
    adaptive_enabled: bool = True,
) -> int:
    if not adaptive_enabled:
        return 1
    repeated = len({d.fingerprint for d in diagnostics if d.fingerprint})
    if prior_hint_count >= 4 or repeated >= 3:
        return 3
    if prior_hint_count >= 2 or repeated >= 2:
        return 2
    return 1
