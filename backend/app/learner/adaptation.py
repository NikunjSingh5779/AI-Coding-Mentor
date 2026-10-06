"""Rule-based hint adaptation from the mistake record (FR-18).

Deterministic rules only (no ML): the learner's recurring categories adjust
how hints are phrased. Fed into prompt_builder as a profile summary.
Switch: ADAPTATION_ENABLED.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from typing import Any


@dataclass
class AdaptationProfile:
    """Derived adaptation for one learner."""

    recurring_categories: list[str]  # categories seen >= threshold
    total_resolved: int
    suggested_starting_level: int  # skip H1 orientation for experienced flows
    summary_for_prompt: str


def build_profile(
    issue_history: list[dict[str, Any]],
    recurrence_threshold: int = 3,
) -> AdaptationProfile:
    """Derive adaptation from resolved-issue history.

    issue_history: [{category, resolved, ...}, ...]
    """
    categories = Counter(
        str(item.get("category", "UNKNOWN")) for item in issue_history if item.get("category")
    )
    recurring = [c for c, n in categories.most_common() if n >= recurrence_threshold]
    resolved = sum(1 for item in issue_history if item.get("resolved"))

    # A learner who has resolved many issues benefits from H2 as the default
    # entry point (H1 orientation is repetitive for them).
    suggested_level = 2 if resolved >= 5 else 1

    if recurring:
        parts = ", ".join(recurring[:3])
        summary = (
            f"Learner has resolved {resolved} issues; recurring mistake patterns: {parts}. "
            "Prefer concept-level framing and connect new hints to those patterns."
        )
    else:
        summary = f"Learner has resolved {resolved} issues; no strongly recurring patterns yet."

    return AdaptationProfile(
        recurring_categories=recurring,
        total_resolved=resolved,
        suggested_starting_level=suggested_level,
        summary_for_prompt=summary,
    )
