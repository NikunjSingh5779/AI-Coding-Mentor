"""Secret redaction applied before any LLM call and before storing code text."""

from __future__ import annotations

import re

# Patterns are intentionally conservative: better to over-redact than leak.
_SECRET_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("api_key_assignment", re.compile(r"(?i)\b(api[_-]?key|secret|token|password|passwd|pwd)\b\s*[=:]\s*[\"']?[\w\-./+]{8,}")),
    ("bearer", re.compile(r"(?i)\bbearer\s+[\w\-./+]{12,}")),
    ("aws_key", re.compile(r"\bAKIA[0-9A-Z]{16}\b")),
    ("github_pat", re.compile(r"\bgh[pousr]_[A-Za-z0-9]{30,}\b")),
    ("openai", re.compile(r"\bsk-[A-Za-z0-9]{20,}\b")),
    ("slack", re.compile(r"\bxox[baprs]-[A-Za-z0-9\-]{10,}\b")),
    ("private_key_block", re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----[\s\S]*?-----END [A-Z ]*PRIVATE KEY-----")),
    ("url_credentials", re.compile(r"\b\w+:\w+@(?:[\w\-]+\.)+\w+")),
    ("jwt", re.compile(r"\bey[A-Za-z0-9_\-]{10,}\.[A-Za-z0-9_\-]{10,}\.[A-Za-z0-9_\-]{10,}\b")),
]


def redact(text: str) -> str:
    """Replace secret-looking substrings with [REDACTED]. Idempotent."""
    if not text:
        return text
    for _, pattern in _SECRET_PATTERNS:
        text = pattern.sub("[REDACTED]", text)
    return text


def contains_secret(text: str) -> bool:
    """True if the text matches any secret pattern."""
    if not text:
        return False
    return any(p.search(text) for _, p in _SECRET_PATTERNS)
