"""Learner tracking: issue lifecycle and checkpoint persistence driven by events.

Subscribes to the analysis flow; stores issue open/update/resolve records and
code checkpoints (redacted) per session. Honours STORE_CODE_TEXT: when false,
only diagnostics and hint metadata are kept, never code text (privacy).
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any

from app.config import get_settings
from app.core.logging import get_logger
from app.ingest.redaction import redact

logger = get_logger(__name__)


@dataclass
class IssueLifecycle:
    """Lifecycle record of one tracked issue."""

    issue_id: str
    category: str
    line: int
    opened_at: float
    last_seen_at: float
    resolved_at: float | None = None
    hints_shown: list[int] = field(default_factory=list)

    @property
    def is_resolved(self) -> bool:
        return self.resolved_at is not None

    @property
    def time_to_resolve_s(self) -> float | None:
        if self.resolved_at is None:
            return None
        return round(self.resolved_at - self.opened_at, 2)


class LearnerTracker:
    """In-memory issue lifecycle tracking; DB persistence via repositories.

    Single-process app (Q5): in-memory state is authoritative during a
    session, and checkpoints are flushed to the database on resolve, hint
    and session end (driven by the analysis flow, not a separate thread).
    """

    def __init__(self, session_token: str):
        self.session_token = session_token
        self.issues: dict[str, IssueLifecycle] = {}
        self.checkpoints: list[dict[str, Any]] = []
        self._settings = get_settings()

    def observe_diagnostics(self, diagnostics: list[dict[str, Any]]) -> None:
        """Update issue lifecycles from one diagnostics batch."""
        now = time.time()
        seen: set[str] = set()
        for d in diagnostics:
            issue_id = str(d.get("fingerprint") or d.get("id") or "")
            if not issue_id:
                continue
            seen.add(issue_id)
            rec = self.issues.get(issue_id)
            if rec is None:
                rec = IssueLifecycle(
                    issue_id=issue_id,
                    category=str(d.get("category", "UNKNOWN")),
                    line=int((d.get("range", {}).get("start", {}) or {}).get("line", 1)),
                    opened_at=now,
                    last_seen_at=now,
                )
                self.issues[issue_id] = rec
                logger.info(
                    "Issue opened",
                    extra={"session": self.session_token, "issue_id": issue_id, "category": rec.category},
                )
            else:
                rec.last_seen_at = now

        for issue_id, rec in self.issues.items():
            if issue_id not in seen and not rec.is_resolved:
                rec.resolved_at = now
                logger.info(
                    "Issue resolved",
                    extra={
                        "session": self.session_token,
                        "issue_id": issue_id,
                        "time_to_resolve_s": rec.time_to_resolve_s,
                    },
                )

    def record_hint_shown(self, issue_id: str, level: int) -> None:
        rec = self.issues.get(issue_id)
        if rec:
            rec.hints_shown.append(level)

    def record_checkpoint(self, code: str, kind: str) -> None:
        """Persist a code checkpoint (redacted) unless code storage is disabled."""
        if not self._settings.store_code_text:
            return
        self.checkpoints.append(
            {
                "code": redact(code),
                "kind": kind,  # run | hint_request | resolve | session_end
                "at": time.time(),
            }
        )

    def summary(self) -> dict[str, Any]:
        """Aggregate summary for the progress endpoints (PH6 consumes this)."""
        all_issues = list(self.issues.values())
        resolved = [r for r in all_issues if r.is_resolved]
        return {
            "session_token": self.session_token,
            "total_issues": len(all_issues),
            "resolved_issues": len(resolved),
            "open_issues": len(all_issues) - len(resolved),
            "avg_time_to_resolve_s": (
                round(sum(r.time_to_resolve_s or 0 for r in resolved) / len(resolved), 2)
                if resolved
                else 0.0
            ),
            "total_hints": sum(len(r.hints_shown) for r in all_issues),
            "checkpoints": len(self.checkpoints),
        }


# Session-keyed tracker registry (single-process app).
_trackers: dict[str, LearnerTracker] = {}


def get_tracker(session_token: str) -> LearnerTracker:
    if session_token not in _trackers:
        _trackers[session_token] = LearnerTracker(session_token)
    return _trackers[session_token]


def reset_trackers() -> None:
    _trackers.clear()
