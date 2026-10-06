"""Rate limits and budgets (P-15) for API and mentor calls.

Single-process app (Q5): an in-memory token bucket is sufficient. Every
limiter is deterministic and unit-testable via an injectable clock.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field


@dataclass
class TokenBucket:
    """Token bucket: `capacity` tokens, refilled at `refill_per_second`."""

    capacity: int
    refill_per_second: float
    tokens: float = 0.0
    last_refill: float = field(default_factory=time.monotonic)

    def _refill(self, now: float) -> None:
        elapsed = max(0.0, now - self.last_refill)
        self.tokens = min(self.capacity, self.tokens + elapsed * self.refill_per_second)
        self.last_refill = now

    def allow(self, cost: float = 1.0, now: float | None = None) -> bool:
        now = time.monotonic() if now is None else now
        self._refill(now)
        if self.tokens >= cost:
            self.tokens -= cost
            return True
        return False


class RateLimiter:
    """Per-session token buckets."""

    def __init__(self, capacity: int = 60, refill_per_second: float = 1.0):
        self.capacity = capacity
        self.refill_per_second = refill_per_second
        self._buckets: dict[str, TokenBucket] = {}

    def allow(self, key: str, cost: float = 1.0) -> bool:
        bucket = self._buckets.get(key)
        if bucket is None:
            bucket = TokenBucket(
                capacity=self.capacity,
                refill_per_second=self.refill_per_second,
                tokens=float(self.capacity),  # start full
            )
            self._buckets[key] = bucket
        return bucket.allow(cost)

    def reset(self, key: str | None = None) -> None:
        if key is None:
            self._buckets.clear()
        else:
            self._buckets.pop(key, None)


# Hints are the expensive path (they may reach an LLM).
hint_rate_limiter = RateLimiter(capacity=30, refill_per_second=0.5)
