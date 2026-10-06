"""Trigger policy: decide when the mentor speaks.

Pure, deterministic rules per 03-ARCHITECTURE.md section 8.1:
- settle:   only after the learner stopped typing for `settle_ms`
- persist:  the same issue must persist across snapshots
- cooldown: per-issue minimum seconds between messages
- explicit: learner requests always pass
- proactivity modes: quiet (explicit only), balanced (default rules),
  proactive (lower thresholds).
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class TriggerContext:
    """Everything the trigger policy needs to decide."""

    proactivity: str  # quiet | balanced | proactive
    settled_ms: int
    issue_seen_in_snapshots: int  # consecutive snapshots the issue appeared in
    seconds_since_last_hint_for_issue: float | None
    explicit_request: bool
    code_grew_since_last_hint: bool = True


@dataclass
class TriggerConfig:
    settle_ms_balanced: int = 1200
    settle_ms_proactive: int = 600
    min_snapshots_balanced: int = 2
    min_snapshots_proactive: int = 1
    cooldown_seconds: float = 20.0


def should_trigger(ctx: TriggerContext, cfg: TriggerConfig) -> tuple[bool, str]:
    """Return (trigger?, reason). Deterministic and side-effect free."""
    if ctx.explicit_request:
        return True, "explicit_request"

    if ctx.proactivity == "quiet":
        return False, "quiet_mode"

    settle_ms = cfg.settle_ms_balanced if ctx.proactivity == "balanced" else cfg.settle_ms_proactive
    min_snaps = cfg.min_snapshots_balanced if ctx.proactivity == "balanced" else cfg.min_snapshots_proactive

    if ctx.settled_ms < settle_ms:
        return False, "not_settled"
    if ctx.issue_seen_in_snapshots < min_snaps:
        return False, "issue_not_persistent"
    if not ctx.code_grew_since_last_hint:
        return False, "code_did_not_grow"
    if (
        ctx.seconds_since_last_hint_for_issue is not None
        and ctx.seconds_since_last_hint_for_issue < cfg.cooldown_seconds
    ):
        return False, "cooldown"

    return True, "triggered"
