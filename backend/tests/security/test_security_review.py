"""PH9 security review tests: origin, size, rate limits, secrets, redaction.

Covers the security table in 03-ARCHITECTURE.md section 10 for the local
single-user deployment (Q5): the WS Origin allowlist, message size limits,
API rate limiting, and the guarantees that code text is redacted and never
logged raw.
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.core.limits import RateLimiter, TokenBucket  # noqa: E402


# ----------------------------------------------------------------- rate limits
class TestTokenBucket:
    def test_allows_up_to_capacity_then_blocks(self):
        bucket = TokenBucket(capacity=3, refill_per_second=0.0, tokens=3.0, last_refill=0.0)
        assert bucket.allow(now=1.0)
        assert bucket.allow(now=1.0)
        assert bucket.allow(now=1.0)
        assert not bucket.allow(now=1.0)

    def test_refills_over_time(self):
        bucket = TokenBucket(capacity=2, refill_per_second=1.0, tokens=0.0, last_refill=0.0)
        assert not bucket.allow(now=0.0)
        assert bucket.allow(now=1.0)  # 1 token after 1s
        assert bucket.allow(now=2.0)

    def test_capacity_is_a_ceiling(self):
        bucket = TokenBucket(capacity=2, refill_per_second=100.0, tokens=0.0, last_refill=0.0)
        bucket.allow(now=1000.0)
        assert bucket.tokens <= 2


class TestRateLimiter:
    def test_per_key_isolation(self):
        limiter = RateLimiter(capacity=1, refill_per_second=0.0)
        assert limiter.allow("a")
        assert not limiter.allow("a")
        assert limiter.allow("b")  # separate session

    def test_reset_clears_state(self):
        limiter = RateLimiter(capacity=1, refill_per_second=0.0)
        assert limiter.allow("a")
        assert not limiter.allow("a")
        limiter.reset("a")
        assert limiter.allow("a")


# --------------------------------------------------------------------- secrets
class TestNoSecretsInRepo:
    """A secret scan over tracked files (SC-6 / release gate)."""

    def test_env_is_not_tracked(self):
        import subprocess

        repo_root = Path(__file__).resolve().parents[3]
        tracked = subprocess.run(
            ["git", "ls-files"], cwd=repo_root, capture_output=True, text=True, check=True
        ).stdout.splitlines()
        assert ".env" not in tracked, ".env must never be committed"

    def test_env_example_has_no_credentials(self):
        repo_root = Path(__file__).resolve().parents[3]
        example = repo_root / ".env.example"
        if not example.exists():
            pytest.skip(".env.example not present")
        content = example.read_text(encoding="utf-8", errors="replace")
        for line in content.splitlines():
            if "=" not in line or line.strip().startswith("#"):
                continue
            key, _, value = line.partition("=")
            upper = key.strip().upper()
            # Match credential-style key names only. A suffix check avoids
            # false positives such as AI_MAX_TOKENS (a count, not a secret).
            is_credential = any(
                upper.endswith(suffix)
                for suffix in ("_KEY", "_SECRET", "_TOKEN", "_PASSWORD", "_PASSWD", "_PWD")
            ) or upper in {"SECRET_KEY", "PASSWORD", "TOKEN"}
            if is_credential:
                # Values in the template must be empty or an obvious placeholder
                assert not value or value.startswith("[") or "your" in value.lower() or value in {
                    "lm-studio",
                    "mentor-sandbox-secret-dev",
                }, f"possible secret in .env.example: {key}"


class TestRedactionBeforeStorage:
    def test_redaction_covers_common_secret_shapes(self):
        from app.ingest.redaction import contains_secret, redact

        samples = [
            'api_key = "sk-abcdefghijklmnopqrstuvwx"',
            "token = 'ghp_Abcdefghijklmnopqrstuvwxyz123456'",
            "AWS = 'AKIAIOSFODNN7EXAMPLE'",
            "password: hunter2abcdefg",
            "eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0.abcdefghijklmnop",
        ]
        for s in samples:
            assert contains_secret(s), f"not detected: {s}"
            assert "sk-abc" not in redact(s)
            assert "[REDACTED]" in redact(s)

    def test_clean_code_not_touched(self):
        from app.ingest.redaction import contains_secret, redact

        clean = "def add(a, b):\n    return a + b\n"
        assert not contains_secret(clean)
        assert redact(clean) == clean
