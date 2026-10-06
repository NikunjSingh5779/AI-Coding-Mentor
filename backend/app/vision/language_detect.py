"""Language guess by parse score when the frame does not declare one (FR-20)."""

from __future__ import annotations

from app.analysis.treesitter.parser import get_parser

# Languages with registered grammars to test against.
_CANDIDATE_LANGUAGES = ["python"]


def detect_language(code: str) -> str:
    """Parse the text with each available grammar; best parse score wins.

    Score = fraction of non-ERROR nodes. Returns 'python' as the fallback
    default (single-language release, Q2).
    """
    scores: dict[str, float] = {}
    for lang in _CANDIDATE_LANGUAGES:
        parser = get_parser(lang)
        if parser is None:
            continue
        tree = parser.parse(code.encode("utf-8", errors="replace"))
        root = tree.root_node

        stats = {"total": 0, "errors": 0}

        def count(node, stats=stats):
            stats["total"] += 1
            if node.type == "ERROR" or node.is_missing:
                stats["errors"] += 1
            for child in node.children:
                count(child, stats)

        count(root)
        scores[lang] = 1.0 - (stats["errors"] / stats["total"] if stats["total"] else 1.0)

    if not scores:
        return "python"
    return max(scores, key=scores.get)
