"""Mentor engine unit tests: tracking, fallback chain, budgets, cache."""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.mentor.engine import IssueRecord, MentorBudget, MentorEngine  # noqa: E402
from app.mentor.llm.base import LLMError, LLMProvider, LLMResult, LLMUnavailable  # noqa: E402
from app.mentor.llm.registry import reset_llm_provider  # noqa: E402


class FakeProvider(LLMProvider):
    name = "fake"

    def __init__(self, text: str = '{"hint": "Consider the loop bounds near line 3."}', fail: bool = False):
        self.text = text
        self.fail = fail
        self.calls = 0

    async def complete(self, system: str, user: str, max_tokens: int) -> LLMResult:
        self.calls += 1
        if self.fail:
            raise LLMError("backend down")
        return LLMResult(text=self.text, model="fake-model", provider="fake", latency_ms=5.0)

    async def is_ready(self) -> bool:
        return not self.fail


class BrokenProvider(FakeProvider):
    """Outputs code fences at H1 — must be rejected by guardrails."""

    def __init__(self):
        super().__init__(text='{"hint": "Do this: ```python\\nreturn sorted(x)\\n```"}')


@pytest.fixture(autouse=True)
def _reset_registry():
    reset_llm_provider()
    yield
    reset_llm_provider()


def _diag(fp: str = "fp1", category: str = "SYNTAX_MISSING_TOKEN", line: int = 3):
    from app.schemas.diagnostic import Diagnostic, DiagnosticRange, Origin, Position, Severity

    return Diagnostic(
        id=fp,
        origin=Origin.PARSER,
        category=category,
        severity=Severity.ERROR,
        message_raw="expected ':'",
        range=DiagnosticRange(start=Position(line=line, col=1), end=Position(line=line, col=5)),
        fingerprint=fp,
    )


def _engine(monkeypatch, provider=None) -> MentorEngine:
    monkeypatch.setenv("LLM_ENABLED", "true")
    from app.config import get_settings

    get_settings.cache_clear()
    eng = MentorEngine(provider=provider or FakeProvider(), budget=MentorBudget(session_limit=10, day_limit=10))
    return eng


@pytest.mark.asyncio
async def test_template_hint_when_llm_disabled(monkeypatch):
    monkeypatch.setenv("LLM_ENABLED", "false")
    from app.config import get_settings

    get_settings.cache_clear()
    eng = MentorEngine(provider=FakeProvider(), budget=MentorBudget(session_limit=5, day_limit=5))
    eng.track_issues(1, [_diag()])
    hint, notice = await eng.generate_hint("fp1", None, "x ==", [])
    assert hint is not None
    assert hint.source.value == "template"
    assert hint.level == 1
    assert notice is None
    assert ":" in hint.text or "expected" in hint.text


@pytest.mark.asyncio
async def test_llm_hint_generated_when_enabled(monkeypatch):
    eng = _engine(monkeypatch)
    eng.track_issues(1, [_diag()])
    hint, notice = await eng.generate_hint("fp1", None, "x ==", [])
    assert hint is not None and hint.source.value == "llm"
    assert hint.level == 1
    # Ladder advanced
    assert eng.get_ladder("fp1").max_level_shown == 1


@pytest.mark.asyncio
async def test_guardrail_rejection_falls_back_to_template(monkeypatch):
    eng = _engine(monkeypatch, provider=BrokenProvider())
    eng.track_issues(1, [_diag()])
    hint, notice = await eng.generate_hint("fp1", None, "x ==", [])
    assert hint is not None
    assert hint.source.value == "template"
    assert "```" not in hint.text


@pytest.mark.asyncio
async def test_llm_failure_falls_back_to_template(monkeypatch):
    eng = _engine(monkeypatch, provider=FakeProvider(fail=True))
    eng.track_issues(1, [_diag()])
    hint, notice = await eng.generate_hint("fp1", None, "x ==", [])
    assert hint is not None and hint.source.value == "template"


@pytest.mark.asyncio
async def test_ladder_progresses_per_issue(monkeypatch):
    eng = _engine(monkeypatch)
    eng.track_issues(1, [_diag()])
    h1, _ = await eng.generate_hint("fp1", None, "x ==", [])
    assert h1.level == 1
    h2, _ = await eng.generate_hint("fp1", None, "x ==", [])
    assert h2.level == 2
    h3, _ = await eng.generate_hint("fp1", None, "x ==", [])
    assert h3.level == 3
    # No auto-escalation to H4
    h4, notice = await eng.generate_hint("fp1", None, "x ==", [])
    assert h4 is None
    assert notice == "already_shown"


@pytest.mark.asyncio
async def test_h4_requires_explicit_request_and_confirmation(monkeypatch):
    eng = _engine(monkeypatch)
    eng.track_issues(1, [_diag()])
    for _ in range(3):
        await eng.generate_hint("fp1", None, "x ==", [])
    # Request H4 without confirmation
    hint, notice = await eng.generate_hint("fp1", 4, "x ==", [], confirmed=False)
    assert hint is None and notice == "h4_needs_confirmation"
    # With confirmation
    hint, notice = await eng.generate_hint("fp1", 4, "x ==", [], confirmed=True)
    assert hint is not None and hint.level == 4
    assert hint.contains_solution


@pytest.mark.asyncio
async def test_h4_blocked_before_h3(monkeypatch):
    eng = _engine(monkeypatch)
    eng.track_issues(1, [_diag()])
    hint, notice = await eng.generate_hint("fp1", 4, "x ==", [], confirmed=True)
    assert hint is None
    assert notice and "ladder_error" in notice


@pytest.mark.asyncio
async def test_budget_exhaustion_uses_template(monkeypatch):
    eng = _engine(monkeypatch, provider=FakeProvider())
    eng.budget = MentorBudget(session_limit=1, day_limit=1)
    eng.track_issues(1, [_diag()])
    h1, _ = await eng.generate_hint("fp1", None, "x ==", [])
    assert h1.source.value == "llm"
    eng.get_ladder("fp1").max_level_shown = 0  # reset ladder to force generation again
    eng.cache.clear()  # also bypass the cache so we exercise the budget path
    eng.track_issues(2, [_diag()])
    h2, _ = await eng.generate_hint("fp1", 1, "x ==", [])
    assert h2.source.value == "template"


@pytest.mark.asyncio
async def test_issue_resolution_and_reopen(monkeypatch):
    eng = _engine(monkeypatch)
    eng.track_issues(1, [_diag()])
    eng.track_issues(2, [])  # issue disappears -> resolved
    assert eng._issues["fp1"].resolved
    eng.track_issues(3, [_diag()])
    assert not eng._issues["fp1"].resolved
    assert eng._issues["fp1"].consecutive_snapshots == 1


@pytest.mark.asyncio
async def test_cache_hit_skips_llm(monkeypatch):
    eng = _engine(monkeypatch)
    eng.track_issues(1, [_diag()])
    h1, _ = await eng.generate_hint("fp1", None, "x ==", [])
    calls_after_first = eng.provider.calls
    # Reset ladder but keep same code/diags/level -> cache hit
    eng.get_ladder("fp1").max_level_shown = 0
    h2, _ = await eng.generate_hint("fp1", 1, "x ==", [])
    assert h2.source.value == "cache"
    assert eng.provider.calls == calls_after_first


@pytest.mark.asyncio
async def test_flat_frontend_diagnostic_shape_keeps_line_and_message(monkeypatch):
    """Regression: the frontend sends flat dicts (line/column/message), not
    nested backend Diagnostics. The hint must use the real line and message,
    not silently default to line 1 with an empty message."""
    eng = _engine(monkeypatch, provider=FakeProvider(fail=True))
    flat = [
        {
            "category": "SYNTAX_UNEXPECTED_TOKEN",
            "line": 7,
            "column": 5,
            "message": "invalid syntax",
            "severity": "error",
            "fingerprint": "SYNTAX_UNEXPECTED_TOKEN:7:5",
        }
    ]
    eng.track_issues(seq=1, diagnostics=flat)
    rec = eng._issues["SYNTAX_UNEXPECTED_TOKEN:7:5"]
    assert rec.line == 7
    assert rec.message == "invalid syntax"

    hint, _ = await eng.generate_hint("SYNTAX_UNEXPECTED_TOKEN:7:5", None, "def f(\n", flat)
    assert hint is not None
    assert "line 7" in hint.text


@pytest.mark.asyncio
async def test_hint_text_is_redacted(monkeypatch):
    eng = _engine(monkeypatch, provider=FakeProvider(text='{"hint": "Your key sk-abcdefghijklmnopqrst looks leaked."}'))
    eng.track_issues(1, [_diag()])
    hint, _ = await eng.generate_hint("fp1", None, "x ==", [])
    assert "sk-abcdefghijklmnopqrst" not in hint.text
