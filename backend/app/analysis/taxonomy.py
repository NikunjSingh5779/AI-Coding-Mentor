"""
Mistake Taxonomy and Category Mappings for AI Coding Mentor.
Maps tool-specific rule codes to language-agnostic categories per 03-ARCHITECTURE.md section 6.4.
"""

from enum import Enum
from typing import Dict, Optional, NamedTuple


class CategoryGroup(str, Enum):
    SYNTAX = "syntax"
    NAME = "name"
    TYPE = "type"
    RUNTIME = "runtime"
    LOGIC = "logic"
    QUALITY = "quality"
    PERFORMANCE = "performance"
    ENVIRONMENT = "environment"


class Category(str, Enum):
    # Syntax errors
    SYNTAX_MISSING_TOKEN = "SYNTAX_MISSING_TOKEN"
    SYNTAX_UNEXPECTED_TOKEN = "SYNTAX_UNEXPECTED_TOKEN"
    SYNTAX_INDENTATION = "SYNTAX_INDENTATION"

    # Name / Scope errors
    NAME_UNDEFINED = "NAME_UNDEFINED"
    IMPORT_UNRESOLVED = "IMPORT_UNRESOLVED"

    # Type / Argument errors
    TYPE_MISMATCH = "TYPE_MISMATCH"
    ARGUMENT_ERROR = "ARGUMENT_ERROR"

    # Runtime errors
    RUNTIME_INDEX = "RUNTIME_INDEX"
    RUNTIME_KEY = "RUNTIME_KEY"
    RUNTIME_NULL = "RUNTIME_NULL"
    RUNTIME_ZERO_DIVISION = "RUNTIME_ZERO_DIVISION"
    RUNTIME_RECURSION = "RUNTIME_RECURSION"
    RUNTIME_TIMEOUT = "RUNTIME_TIMEOUT"
    RUNTIME_MEMORY = "RUNTIME_MEMORY"
    RUNTIME_OTHER = "RUNTIME_OTHER"

    # Logic errors
    LOGIC_WRONG_OUTPUT = "LOGIC_WRONG_OUTPUT"
    LOGIC_SUSPICION = "LOGIC_SUSPICION"

    # Quality / Style issues
    QUALITY_UNUSED = "QUALITY_UNUSED"
    QUALITY_STYLE = "QUALITY_STYLE"
    QUALITY_COMPLEXITY = "QUALITY_COMPLEXITY"

    # Performance issues
    PERF_NESTED_LOOP = "PERF_NESTED_LOOP"
    PERF_REPEATED_WORK = "PERF_REPEATED_WORK"

    # Environment issues
    ENV_UNSUPPORTED = "ENV_UNSUPPORTED"


class CategoryInfo(NamedTuple):
    group: CategoryGroup
    description: str
    default_severity: str


CATEGORY_METADATA: Dict[Category, CategoryInfo] = {
    Category.SYNTAX_MISSING_TOKEN: CategoryInfo(
        CategoryGroup.SYNTAX, "Missing syntax token (e.g., ':', ')', ']')", "error"
    ),
    Category.SYNTAX_UNEXPECTED_TOKEN: CategoryInfo(
        CategoryGroup.SYNTAX, "Unexpected token or invalid syntax", "error"
    ),
    Category.SYNTAX_INDENTATION: CategoryInfo(
        CategoryGroup.SYNTAX, "Inconsistent or invalid indentation", "error"
    ),
    Category.NAME_UNDEFINED: CategoryInfo(
        CategoryGroup.NAME, "Undefined name or misspelled variable", "error"
    ),
    Category.IMPORT_UNRESOLVED: CategoryInfo(
        CategoryGroup.NAME, "Unresolved import or module not found", "error"
    ),
    Category.TYPE_MISMATCH: CategoryInfo(
        CategoryGroup.TYPE, "Type mismatch operation", "error"
    ),
    Category.ARGUMENT_ERROR: CategoryInfo(
        CategoryGroup.TYPE, "Wrong number or types of arguments", "error"
    ),
    Category.RUNTIME_INDEX: CategoryInfo(
        CategoryGroup.RUNTIME, "Index out of range", "error"
    ),
    Category.RUNTIME_KEY: CategoryInfo(
        CategoryGroup.RUNTIME, "Dictionary key not found", "error"
    ),
    Category.RUNTIME_NULL: CategoryInfo(
        CategoryGroup.RUNTIME, "Operation on None/null value", "error"
    ),
    Category.RUNTIME_ZERO_DIVISION: CategoryInfo(
        CategoryGroup.RUNTIME, "Division by zero", "error"
    ),
    Category.RUNTIME_RECURSION: CategoryInfo(
        CategoryGroup.RUNTIME, "Maximum recursion depth exceeded", "error"
    ),
    Category.RUNTIME_TIMEOUT: CategoryInfo(
        CategoryGroup.RUNTIME, "Execution timed out", "error"
    ),
    Category.RUNTIME_MEMORY: CategoryInfo(
        CategoryGroup.RUNTIME, "Memory limit exceeded", "error"
    ),
    Category.RUNTIME_OTHER: CategoryInfo(
        CategoryGroup.RUNTIME, "Other uncaught runtime error", "error"
    ),
    Category.LOGIC_WRONG_OUTPUT: CategoryInfo(
        CategoryGroup.LOGIC, "Output differs from expected result", "error"
    ),
    Category.LOGIC_SUSPICION: CategoryInfo(
        CategoryGroup.LOGIC, "Suspected logic or edge case issue", "suspicion"
    ),
    Category.QUALITY_UNUSED: CategoryInfo(
        CategoryGroup.QUALITY, "Unused variable or import", "warning"
    ),
    Category.QUALITY_STYLE: CategoryInfo(
        CategoryGroup.QUALITY, "Style or naming convention violation", "info"
    ),
    Category.QUALITY_COMPLEXITY: CategoryInfo(
        CategoryGroup.QUALITY, "Code complexity or deep nesting", "info"
    ),
    Category.PERF_NESTED_LOOP: CategoryInfo(
        CategoryGroup.PERFORMANCE, "Potentially expensive nested loops", "warning"
    ),
    Category.PERF_REPEATED_WORK: CategoryInfo(
        CategoryGroup.PERFORMANCE, "Repeated computation inside a loop", "warning"
    ),
    Category.ENV_UNSUPPORTED: CategoryInfo(
        CategoryGroup.ENVIRONMENT, "Package or environment feature unsupported", "error"
    ),
}

# Rule code mappings for tools (Ruff, Pyflakes, etc.)
RUFF_RULE_MAPPING: Dict[str, Category] = {
    # Pyflakes
    "F401": Category.QUALITY_UNUSED,          # unused import
    "F821": Category.NAME_UNDEFINED,          # undefined name
    "F841": Category.QUALITY_UNUSED,          # unused local variable
    "F811": Category.NAME_UNDEFINED,          # redefinition
    "F706": Category.SYNTAX_UNEXPECTED_TOKEN, # return outside function
    "F704": Category.SYNTAX_UNEXPECTED_TOKEN, # yield outside function

    # pycodestyle errors
    "E999": Category.SYNTAX_UNEXPECTED_TOKEN, # SyntaxError
    "E111": Category.SYNTAX_INDENTATION,      # indentation is not a multiple of 4
    "E112": Category.SYNTAX_INDENTATION,      # expected an indented block
    "E113": Category.SYNTAX_INDENTATION,      # unexpected indentation
    "E117": Category.SYNTAX_INDENTATION,      # over-indented
    "E722": Category.QUALITY_STYLE,           # bare except
    "E501": Category.QUALITY_STYLE,           # line too long

    # PEP 8 Naming
    "N801": Category.QUALITY_STYLE,           # class name should use CapWords
    "N802": Category.QUALITY_STYLE,           # function name should be lowercase
    "N803": Category.QUALITY_STYLE,           # argument name should be lowercase
    "N806": Category.QUALITY_STYLE,           # variable in function should be lowercase
}


def map_rule_to_category(
    rule: Optional[str],
    default: Category = Category.QUALITY_STYLE,
) -> Category:
    """Map a tool rule string to a taxonomy category without inventing syntax errors."""
    if not rule:
        return default

    explicit = RUFF_RULE_MAPPING.get(rule)
    if explicit is not None:
        return explicit

    # Unknown Ruff rules are still linter findings. Treat E/W/N/F families
    # as quality findings rather than syntax failures; parser-level E999 is
    # explicitly mapped above.
    if rule.startswith(("E", "W", "N", "F")):
        return Category.QUALITY_STYLE

    return default
