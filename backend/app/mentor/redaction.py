from __future__ import annotations

import re

def redact_secrets(text: str) -> str:
    patterns = [
        r"(?i)sk-[A-Za-z0-9_-]{20,}",
        r"(?i)ghp_[A-Za-z0-9_]{20,}",
        r"(?i)api[_-]?key\s*[=:]\s*['\"][^'\"]+['\"]",
        r"(?i)authorization\s*:\s*bearer\s+[A-Za-z0-9._-]+",
    ]
    result = text
    for pattern in patterns:
        result = re.sub(pattern, "[REDACTED_SECRET]", result)
    return result

def safe_hint_text(text: str, max_chars: int, allow_solution: bool) -> str:
    value = redact_secrets(text).strip()
    if not allow_solution:
        value = re.sub(r"\`\`\`[\\s\\S]*?\`\`\`", "[code omitted]", value)
    return value[:max_chars].rstrip()
