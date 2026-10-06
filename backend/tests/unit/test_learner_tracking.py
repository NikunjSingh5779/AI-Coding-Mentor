"""Learner tracking unit tests + privacy guarantees (SC-6 partial)."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.learner.tracking import LearnerTracker, get_tracker, reset_trackers  # noqa: E402


def _diag(fp: str, category: str = "SYNTAX_MISSING_TOKEN", line: int = 3) -> dict:
    return {
        "fingerprint": fp,
        "id": fp,
        "category": category,
        "severity": "error",
        "message_raw": "expected ':'",
        "range": {"start": {"line": line, "col": 1}, "end": {"line": line, "col": 5}},
    }


class TestIssueLifecycle:
    def test_issue_opens_and_resolves(self):
        t = LearnerTracker("s1")
        t.observe_diagnostics([_diag("a")])
        assert len(t.issues) == 1
        assert not t.issues["a"].is_resolved
        t.observe_diagnostics([])  # issue gone -> resolved
        assert t.issues["a"].is_resolved
        assert t.issues["a"].time_to_resolve_s is not None

    def test_issue_stays_open_across_snapshots(self):
        t = LearnerTracker("s1")
        t.observe_diagnostics([_diag("a")])
        t.observe_diagnostics([_diag("a")])
        assert not t.issues["a"].is_resolved

    def test_summary_counts(self):
        t = LearnerTracker("s1")
        t.observe_diagnostics([_diag("a"), _diag("b", category="NAME_UNDEFINED")])
        t.observe_diagnostics([_diag("a")])  # b resolved
        t.record_hint_shown("a", 1)
        t.record_hint_shown("a", 2)
        s = t.summary()
        assert s["total_issues"] == 2
        assert s["resolved_issues"] == 1
        assert s["open_issues"] == 1
        assert s["total_hints"] == 2


class TestPrivacy:
    def test_checkpoint_redacts_secrets(self):
        t = LearnerTracker("s1")
        t.record_checkpoint('API_KEY = "ghp_Abcdefghijklmnopqrstuvwxyz123456"', kind="run")
        assert "ghp_" not in t.checkpoints[0]["code"]
        assert "[REDACTED]" in t.checkpoints[0]["code"]

    def test_store_code_text_false_never_stores_code(self, monkeypatch):
        monkeypatch.setenv("STORE_CODE_TEXT", "false")
        from app.config import get_settings

        get_settings.cache_clear()
        try:
            t = LearnerTracker("s1")
            t.record_checkpoint("secret_code = 1", kind="run")
            assert t.checkpoints == []
        finally:
            get_settings.cache_clear()

    def test_summary_contains_no_code(self):
        t = LearnerTracker("s1")
        t.observe_diagnostics([_diag("a")])
        t.record_checkpoint("x = 1", kind="run")
        import json

        blob = json.dumps(t.summary())
        assert "x = 1" not in blob
        assert "code" not in json.loads(blob)


class TestRegistry:
    def test_tracker_registry_per_session(self):
        reset_trackers()
        t1 = get_tracker("s1")
        t2 = get_tracker("s1")
        t3 = get_tracker("s2")
        assert t1 is t2
        assert t1 is not t3
        reset_trackers()
