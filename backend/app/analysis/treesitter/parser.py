"""
Tree-sitter parser registry and interface.
Provides grammar registry per language.
"""

from typing import Dict, Optional, Any
import threading
import tree_sitter

# Language objects are immutable and safe to cache. Parser instances are kept
# thread-local because the fast pipeline invokes analyzers concurrently.
_LANGUAGES: Dict[str, Any] = {}
_PARSER_LOCAL = threading.local()


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
    parsers = getattr(_PARSER_LOCAL, "parsers", None)
    if parsers is None:
        parsers = {}
        _PARSER_LOCAL.parsers = parsers

    if lang_name in parsers:
        return parsers[lang_name]

    language = get_language(lang_name)
    if language is None:
        return None

    try:
        parser = tree_sitter.Parser(language)
    except Exception:
        # Compatibility fallback for older/newer tree_sitter API.
        try:
            parser = tree_sitter.Parser()
            parser.set_language(language)
        except Exception:
            return None

    parsers[lang_name] = parser
    return parser


def parse_code(code: str, language: str = "python") -> Optional[Any]:
    """Parse source code string with Tree-sitter."""
    parser = get_parser(language)
    if not parser:
        return None
    try:
        return parser.parse(bytes(code, "utf-8"))
    except Exception:
        return None
