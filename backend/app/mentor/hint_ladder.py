"""Hint ladder: per-issue hint-level state machine (H1-H4).

Ladder rules (Q13, 03-ARCHITECTURE.md section 8.2):
- Levels progress H1 -> H2 -> H3 -> H4.
- H4 (solution reveal) requires: H3 was shown AND an explicit learner request
  AND a confirmation flag. No automatic escalation, ever.
"""

from __future__ import annotations

from dataclasses import dataclass, field


class LadderError(ValueError):
    """Invalid ladder transition requested."""


@dataclass
class IssueLadderState:
    """Ladder state for one issue."""

    issue_id: str
    max_level_shown: int = 0
    h4_requested: bool = False
    h4_confirmed: bool = False
    history: list[int] = field(default_factory=list)

    def next_level(self, requested: int | None = None) -> int | None:
        """Compute the next level to generate, or None if none may be generated.

        `requested` is the level the learner explicitly asked for (if any).
        """
        if requested is not None:
            if requested == 4:
                if self.max_level_shown < 3:
                    raise LadderError("H4 requires H3 to have been shown first")
                if not self.h4_requested:
                    raise LadderError("H4 requires an explicit learner request")
                # Confirmation (the click after the request) is enforced by
                # the engine, not the ladder state machine.
                return 4
            if requested in (1, 2, 3):
                if requested <= self.max_level_shown:
                    return None  # already shown; do not repeat
                return requested
            raise LadderError(f"invalid level {requested}")

        # No explicit request: offer the next unshown level, capped at H3.
        nxt = self.max_level_shown + 1
        if nxt > 3:
            return None
        return nxt
