"""Guardrails: enforce hint schema, level compliance, grounding and no-leak rules.

Hard safety rule (CLAUDE.md): levels H1-H3 must contain NO complete solution
and NO fenced code. H4 only on explicit learner request after H3 was shown.
Violations trigger a retry, then a deterministic template fallback.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from app.core.logging import get_logger
from app.ingest.redaction import redact

logger = get_logger(__name__)

_FENCED_CODE = re.compile(r"```|~~~")
_SOLUTION_MARKERS = re.compile(
    r"(?i)\b(here is the (complete|full|fixed) (solution|code)|copy this|just replace (your|the) (function|code) with)"
)

MAX_HINT_CHARS = 800


@dataclass
class GuardrailVerdict:
    """Result of validating one hint against the guardrail rules."""

    ok: bool
    reason: str | None = None
    text: str = ""


def validate_hint(
    text: str,
    level: int,
    issue_id: str,
    known_line: int | None = None,
) -> GuardrailVerdict:
    """Validate a hint for level compliance, leakage and grounding.

    Returns a verdict; `ok=False` means the hint must not be shown.
    """
    if not text or not text.strip():
        return GuardrailVerdict(ok=False, reason="empty")

    text = redact(text).strip()

    if len(text) > MAX_HINT_CHARS:
        return GuardrailVerdict(ok=False, reason="too_long", text=text)

    if level in (1, 2, 3):
        # No fenced code blocks at H1-H3.
        if _FENCED_CODE.search(text):
            return GuardrailVerdict(ok=False, reason="fenced_code", text=text)
        # No "here is the whole solution" phrasing.
        if _SOLUTION_MARKERS.search(text):
            return GuardrailVerdict(ok=False, reason="solution_leak", text=text)
        # Inline code ticks are allowed only for single identifiers.
        inline = re.findall(r"`([^`\n]+)`", text)
        if any(("=" in s or "\n" in s or len(s) > 80) for s in inline):
            return GuardrailVerdict(ok=False, reason="code_in_inline", text=text)

    if level == 4:
        # H4 is the only level allowed to carry code; still redact secrets.
        pass

    if known_line is not None:
        # Grounding check: line references, when present, must be plausible.
        for m in re.finditer(r"line (\d+)", text, re.IGNORECASE):
            if abs(int(m.group(1)) - known_line) > 2:
                return GuardrailVerdict(ok=False, reason="bad_grounding", text=text)

    return GuardrailVerdict(ok=True, text=text)


def validate_output_schema(raw: str) -> str:
    """Extract the hint text from the model output.

    Accepts either a bare string or a JSON object {"hint": "..."}.
    Raises ValueError on unusable output.
    """
    raw = raw.strip()
    if not raw:
        raise ValueError("empty LLM output")
    if raw.startswith("{"):
        import json

        try:
            data = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise ValueError(f"invalid JSON output: {exc}") from exc
        if not isinstance(data, dict) or "hint" not in data:
            raise ValueError("JSON output missing 'hint' key")
        return str(data["hint"]).strip()
    return raw
