from __future__ import annotations

import re
from dataclasses import dataclass

from app.vision.ocr import OCRLine


@dataclass(frozen=True)
class DetectedRegion:
    left: int
    top: int
    width: int
    height: int
    confidence: float
    code: str


CODE_TOKENS = re.compile(
    r"\b(def|class|return|if|elif|else|for|while|import|from|try|except|"
    r"public|private|static|void|int|include|function|const|let|var)\b|"
    r"[{}\[\]();:=<>+\-*/]|=>|::"
)


def _score(line: OCRLine) -> float:
    token_hits = len(CODE_TOKENS.findall(line.text))
    punctuation = sum(char in "{}[]();:=<>+-*/" for char in line.text)
    base = min(1.0, 0.22 + 0.14 * token_hits + 0.04 * punctuation)
    return min(1.0, base * (0.55 + 0.45 * line.confidence))


def detect_code_region(
    lines: list[OCRLine],
    *,
    min_confidence: float = 0.55,
) -> DetectedRegion | None:
    scored = [(line, _score(line)) for line in lines]
    candidates = [(line, score) for line, score in scored if score >= 0.45]
    if len(candidates) < 2:
        return None

    selected = candidates[:30]
    x1 = min(line.left for line, _ in selected)
    y1 = min(line.top for line, _ in selected)
    x2 = max(line.left + line.width for line, _ in selected)
    y2 = max(line.top + line.height for line, _ in selected)
    confidence = sum(score for _, score in selected) / len(selected)

    if confidence < min_confidence:
        return None

    code = "\n".join(line.text for line, _ in selected)
    return DetectedRegion(
        left=max(0, x1 - 8),
        top=max(0, y1 - 8),
        width=max(1, x2 - x1 + 16),
        height=max(1, y2 - y1 + 16),
        confidence=min(1.0, confidence),
        code=code,
    )
