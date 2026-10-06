"""Mentor engine: trigger -> prompt -> LLM -> guardrails -> hint.

Fallback chain: cache -> LLM (guarded) -> template. The engine never emits
an unvalidated LLM output, and template mode works with no LLM at all.
"""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from app.config import get_settings
from app.core.logging import get_logger
from app.mentor.cache import HintCache, compute_prompt_hash
from app.mentor.fallback_explanations import fallback_hint, resolve_category
from app.mentor.guardrails import validate_hint, validate_output_schema
from app.mentor.hint_ladder import IssueLadderState, LadderError
from app.mentor.llm.base import LLMError, LLMProvider
from app.mentor.llm.registry import get_llm_provider
from app.mentor.prompt_builder import PROMPT_VERSION, PromptInput, build_prompt
from app.schemas.hint import HintModel, HintSource

logger = get_logger(__name__)


def _diag_line(d: Any) -> int:
    """Best-effort line extraction from a Diagnostic-like object or dict."""
    if isinstance(d, dict):
        # Flat shape sent by the frontend (line/column) ...
        if d.get("line"):
            return int(d["line"])
        # ... or a nested range (backend Diagnostic shape).
        start = (d.get("range") or {}).get("start") or {}
        return int(start.get("line", 1))

    line = getattr(d, "line", None)
    if line:
        return int(line)
    rng = getattr(d, "range", None)
    start = getattr(rng, "start", None) if rng is not None else None
    if start is not None and getattr(start, "line", None):
        return int(start.line)
    return 1


def _diag_message(d: Any) -> str:
    """Message text from either the flat (frontend) or nested (backend) shape."""
    if isinstance(d, dict):
        return str(d.get("message_raw") or d.get("message") or "")
    return str(getattr(d, "message_raw", "") or "")


@dataclass
class IssueRecord:
    """Runtime record of one tracked issue in a session."""

    issue_id: str
    category: str
    line: int
    message: str
    rule: str = ""
    first_seen_seq: int = 0
    last_seen_seq: int = 0
    consecutive_snapshots: int = 0
    last_hint_at: float | None = None
    resolved: bool = False


@dataclass
class MentorBudget:
    """Session/day LLM budgets (P-15)."""

    session_used: int = 0
    day_used: int = 0
    session_limit: int = 50
    day_limit: int = 200

    def can_spend(self) -> tuple[bool, str]:
        if self.session_used >= self.session_limit:
            return False, "budget_exhausted_session"
        if self.day_used >= self.day_limit:
            return False, "budget_exhausted_day"
        return True, "ok"

    def spend(self) -> None:
        self.session_used += 1
        self.day_used += 1


class MentorEngine:
    """Turns verified diagnostics into guard-railed progressive hints."""

    def __init__(self, provider: LLMProvider | None = None, budget: MentorBudget | None = None):
        self.provider = provider or get_llm_provider()
        self.cache = HintCache()
        settings = get_settings()
        self.budget = budget or MentorBudget(
            session_limit=settings.hosted_llm_budget_session,
            day_limit=settings.hosted_llm_budget_day,
        )
        self._issues: dict[str, IssueRecord] = {}
        self._ladders: dict[str, IssueLadderState] = {}

    # ------------------------------------------------------------------ issues
    def track_issues(self, seq: int, diagnostics: list[Any]) -> dict[str, IssueRecord]:
        """Update tracked issues from a diagnostics batch; returns current map."""
        seen: dict[str, IssueRecord] = {}
        for d in diagnostics:
            fp = getattr(d, "fingerprint", None) or (d.get("fingerprint") if isinstance(d, dict) else None)
            if not fp:
                fp = f"ad-hoc-{len(self._issues)}-{seq}-{len(seen)}"
            rec = self._issues.get(fp)
            if rec is None or rec.resolved:
                raw_category = (
                    getattr(d, "category", None)
                    or (d.get("category", "UNKNOWN") if isinstance(d, dict) else "UNKNOWN")
                )
                # Normalise legacy/tool-specific names to a taxonomy value so
                # hint metadata and templates stay consistent.
                category = resolve_category(str(raw_category)) or str(raw_category)
                rec = IssueRecord(
                    issue_id=fp,
                    category=category,
                    line=_diag_line(d),
                    message=_diag_message(d)[:200],
                    rule=(getattr(d, "rule", None) or (d.get("rule") if isinstance(d, dict) else None) or ""),
                    first_seen_seq=seq,
                )
                self._issues[fp] = rec
            rec.last_seen_seq = seq
            rec.consecutive_snapshots += 1
            rec.resolved = False
            seen[fp] = rec

        # Mark issues absent from this batch as resolved.
        for issue_id, rec in self._issues.items():
            if issue_id not in seen:
                rec.resolved = True

        return seen

    def get_ladder(self, issue_id: str) -> IssueLadderState:
        if issue_id not in self._ladders:
            self._ladders[issue_id] = IssueLadderState(issue_id=issue_id)
        return self._ladders[issue_id]

    # ------------------------------------------------------------------ hints
    async def generate_hint(
        self,
        issue_id: str,
        level: int | None,
        code: str,
        diagnostics: list[dict],
        confirmed: bool = False,
    ) -> tuple[HintModel | None, str | None]:
        """Generate a hint for one issue. Returns (hint, notice).

        notice is a machine-readable reason string when no hint was produced.
        """
        record = self._issues.get(issue_id)
        ladder = self.get_ladder(issue_id)

        # An explicit level-4 request from the learner is the request itself;
        # `confirmed` is the confirmation click that must accompany it.
        if level == 4:
            ladder.h4_requested = True
            ladder.h4_confirmed = confirmed

        try:
            target_level = ladder.next_level(requested=level)
        except LadderError as exc:
            return None, f"ladder_error: {exc}"

        if target_level is None:
            return None, "already_shown"

        if target_level == 4 and not confirmed:
            return None, "h4_needs_confirmation"

        # 1. Cache
        settings = get_settings()
        model_name = getattr(self.provider, "_model", getattr(self.provider, "name", "unknown"))
        phash = compute_prompt_hash(code, diagnostics, target_level, PROMPT_VERSION, model_name)
        cached = self.cache.get(phash)
        if cached:
            return self._make_hint(issue_id, target_level, cached, HintSource.CACHE, 0.0), None

        # 2. LLM path (guarded) — never for template-only mode
        if settings.llm_enabled:
            ok, reason = self.budget.can_spend()
            if ok:
                try:
                    system, user = build_prompt(
                        PromptInput(code=code, diagnostics=diagnostics, level=target_level)
                    )
                    result = await self.provider.complete(system, user, max_tokens=300)
                    text = validate_output_schema(result.text)
                    verdict = validate_hint(
                        text, target_level, issue_id, known_line=record.line if record else None
                    )
                    if verdict.ok:
                        self.cache.put(phash, verdict.text)
                        self.budget.spend()
                        ladder.max_level_shown = target_level
                        return (
                            self._make_hint(issue_id, target_level, verdict.text, HintSource.LLM, result.latency_ms),
                            None,
                        )
                    logger.warning(
                        "Guardrail rejected LLM hint; falling back to template",
                        extra={"reason": verdict.reason, "level": target_level},
                    )
                except (LLMError, ValueError) as exc:
                    logger.warning(
                        "LLM hint generation failed; using template fallback",
                        extra={"error": str(exc)},
                    )
            else:
                logger.info("LLM budget exhausted; using template", extra={"reason": reason})

        # 3. Template fallback (H1-H3 always available)
        if target_level == 4:
            return None, "h4_unavailable_no_llm"
        category = record.category if record else "RUNTIME_OTHER"
        text = fallback_hint(
            category,
            target_level,
            message=record.message if record else "",
            line=record.line if record else 1,
            rule=record.rule if record else "",
        )
        ladder.max_level_shown = target_level
        if record:
            record.last_hint_at = time.time()
        return self._make_hint(issue_id, target_level, text, HintSource.TEMPLATE, 0.0), None

    def _make_hint(
        self, issue_id: str, level: int, text: str, source: HintSource, latency_ms: float
    ) -> HintModel:
        record = self._issues.get(issue_id)
        return HintModel(
            id=str(uuid.uuid4()),
            issue_id=issue_id,
            level=level,
            text=text,
            source=source,
            category=record.category if record else "UNKNOWN",
            created_at=datetime.now(UTC).isoformat(),
            latency_ms=latency_ms,
            contains_solution=(level == 4),
        )
