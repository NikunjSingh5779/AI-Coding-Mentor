"""
Tree-sitter parser registry and interface.
Provides grammar registry per language.
"""

from typing import Dict, Optional, Any
import tree_sitter

# Registry of language parsers
_LANGUAGES: Dict[str, Any] = {}
_PARSERS: Dict[str, tree_sitter.Parser] = {}


def get_language(lang_name: str) -> Optional[Any]:
    """Get or load Tree-sitter Language object for language name."""
    lang_name = lang_name.lower()
    if lang_name in _LANGUAGES:
        return _LANGUAGES[lang_name]

    if lang_name == "python":
        try:
            import tree_sitter_python
            language = tree_sitter.Language(tree_sitter_python.language())
            _LANGUAGES[lang_name] = language
            return language
        except ImportError:
            return None

    return None


def get_parser(lang_name: str) -> Optional[tree_sitter.Parser]:
    """Get or create Tree-sitter Parser for the given language."""
    lang_name = lang_name.lower()
    if lang_name in _PARSERS:
        return _PARSERS[lang_name]

    language = get_language(lang_name)
    if language is None:
        return None

    try:
        parser = tree_sitter.Parser(language)
        _PARSERS[lang_name] = parser
        return parser
    except Exception:
        # Compatibility fallback for older/newer tree_sitter API
        try:
            parser = tree_sitter.Parser()
            parser.set_language(language)
            _PARSERS[lang_name] = parser
            return parser
        except Exception:
            return None


def parse_code(code: str, language: str = "python") -> Optional[Any]:
    """Parse source code string with Tree-sitter."""
    parser = get_parser(language)
    if not parser:
        return None
    try:
        return parser.parse(bytes(code, "utf-8"))
    except Exception:
        return None
