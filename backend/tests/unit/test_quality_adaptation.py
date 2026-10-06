"""Quality analyzer + adaptation tests (PH6)."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.analysis.quality.complexity import analyze_complexity  # noqa: E402
from app.analysis.quality.patterns import analyze_patterns  # noqa: E402
from app.learner.adaptation import build_profile  # noqa: E402


class TestComplexity:
    def test_clean_code_no_diagnostics(self):
        code = "def f(x):\n    if x:\n        return 1\n    return 0\n"
        assert analyze_complexity(code) == []

    def test_deep_nesting_flagged(self):
        code = (
            "def f(a):\n"
            "    if a:\n"
            "        for i in a:\n"
            "            if i:\n"
            "                while i:\n"
            "                    if i:\n"
            "                        return 1\n"
            "    return 0\n"
        )
        diags = analyze_complexity(code)
        assert any(d.rule == "nesting" for d in diags)

    def test_syntax_error_returns_empty(self):
        assert analyze_complexity("def broken(:") == []


class TestPatterns:
    def test_nested_loop_flagged(self):
        code = "def f(n):\n    for i in range(n):\n        for j in range(n):\n            print(i, j)\n"
        diags = analyze_patterns(code)
        assert any(d.category == "PERF_NESTED_LOOP" for d in diags)

    def test_repeated_len_flagged(self):
        code = (
            "def f(items):\n"
            "    total = 0\n"
            "    for x in items:\n"
            "        total += len(items)\n"
            "        total += len(items)\n"
            "        total += len(items)\n"
            "    return total\n"
        )
        diags = analyze_patterns(code)
        assert any(d.category == "PERF_REPEATED_WORK" for d in diags)

    def test_clean_loop_not_flagged(self):
        code = "def f(items):\n    for x in items:\n        print(x)\n"
        assert analyze_patterns(code) == []


class TestAdaptation:
    def test_recurring_categories_detected(self):
        history = [{"category": "SYNTAX_MISSING_TOKEN", "resolved": True} for _ in range(4)]
        profile = build_profile(history)
        assert "SYNTAX_MISSING_TOKEN" in profile.recurring_categories
        assert "SYNTAX_MISSING_TOKEN" in profile.summary_for_prompt

    def test_no_recurring_when_few(self):
        history = [{"category": "NAME_UNDEFINED", "resolved": True}, {"category": "RUNTIME_INDEX", "resolved": True}]
        profile = build_profile(history)
        assert profile.recurring_categories == []

    def test_experienced_learner_starts_at_h2(self):
        history = [{"category": f"C{i}", "resolved": True} for i in range(6)]
        profile = build_profile(history)
        assert profile.suggested_starting_level == 2

    def test_deterministic(self):
        history = [{"category": "A", "resolved": True}, {"category": "A", "resolved": True}, {"category": "A", "resolved": True}]
        p1 = build_profile(history)
        p2 = build_profile(history)
        assert p1.summary_for_prompt == p2.summary_for_prompt
