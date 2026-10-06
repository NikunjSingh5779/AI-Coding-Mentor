"""Template fallback explanations per category for H1-H3 (no LLM needed).

Used when the LLM is disabled, unavailable, or its output fails guardrails.
Plain language for a beginner (Q8). H4 is never template-generated: it needs
the LLM, because a template cannot know the learner's actual solution.
"""

from __future__ import annotations

from app.analysis.taxonomy import Category

# level -> template with {message} / {line} / {rule} slots.
_TEMPLATES: dict[str, dict[int, str]] = {
    # --- Syntax ---
    "SYNTAX_MISSING_TOKEN": {
        1: "Python expected one more character near line {line} — often a missing `:` at the end of an `if`, `for`, `while` or `def` line. Look there first.",
        2: "The parser stopped at line {line} because a required token is missing. Check that every block-opening line ends with `:` and every bracket you opened is closed.",
        3: "The error is on line {line}: {message}. Re-read that line and the one above it character by character — one opening bracket or colon is unmatched.",
    },
    "SYNTAX_UNEXPECTED_TOKEN": {
        1: "Something on or just before line {line} surprised Python. Check for a typo, a stray symbol, or `=` used where `==` was meant.",
        2: "The parser reports an unexpected token around line {line}. This usually means the previous statement is incomplete — compare against a similar line you know is correct.",
        3: "Unexpected token at line {line}: {message}. The real problem is often at the end of the previous line (missing colon, comma or bracket).",
    },
    "SYNTAX_INDENTATION": {
        1: "The indentation on line {line} doesn't line up with the block it belongs to. Python uses consistent 4-space indents.",
        2: "Line {line} is indented differently from its siblings. Pick one indent unit (4 spaces) and make every line in the same block match.",
        3: "Indentation error at line {line}: {message}. Count the leading spaces — mixing tabs and spaces or jumping indent levels causes this.",
    },
    # --- Names ---
    "NAME_UNDEFINED": {
        1: "The name on line {line} is being used before Python knows what it is. Check the spelling — Python is case-sensitive.",
        2: "Line {line} references a name that was never defined in scope. Look for a typo, or a variable you meant to create earlier in the function.",
        3: "`{rule}` on line {line} is undefined: {message}. Verify where you intended to define it, and that it is defined before this line runs.",
    },
    "IMPORT_UNRESOLVED": {
        1: "The import on line {line} can't be resolved. Check the module name for typos.",
        2: "Line {line} imports something unavailable. In this sandbox only the Python standard library is available (Q11).",
        3: "Import error at line {line}: {message}. Confirm the module exists and is allowed — third-party packages are not installed in the sandbox.",
    },
    # --- Types / arguments ---
    "TYPE_MISMATCH": {
        1: "Two incompatible values are being combined on line {line}. Print their types to see what you actually have.",
        2: "Line {line} mixes types that don't work together. A common case: doing arithmetic on a value read as a string — convert it first.",
        3: "Type error on line {line}: {message}. Trace the value back to where it was created and confirm its type is what you expect.",
    },
    "ARGUMENT_ERROR": {
        1: "The function call on line {line} passes the wrong number or kind of arguments. Compare the call with the function's definition.",
        2: "Line {line} calls a function with mismatched arguments. Count the parameters in the definition and check each argument you pass.",
        3: "Argument error on line {line}: {message}. Read the function signature carefully — argument order and required parameters matter.",
    },
    # --- Runtime ---
    "RUNTIME_INDEX": {
        1: "An index on line {line} went past the end of the sequence. Remember the last valid index is length minus 1.",
        2: "Line {line} used an index outside the valid range. Check loop bounds — a common culprit is `<=` where `<` was intended.",
        3: "Index error on line {line}: {message}. Ask what the collection's length is at that moment; consider guarding the access.",
    },
    "RUNTIME_KEY": {
        1: "A dictionary lookup on line {line} used a key that doesn't exist. Check the exact spelling of the key.",
        2: "Line {line} looks up a missing key. Consider checking membership first, or use a lookup that tolerates absence.",
        3: "Key error on line {line}: {message}. Print the dictionary right before the failing line to see the keys it actually has.",
    },
    "RUNTIME_NULL": {
        1: "Line {line} uses a value that is None. Find where the value came from — a function that returned nothing, perhaps.",
        2: "A None reached line {line}. A function without a `return` gives None; check what produced this value.",
        3: "NoneType error on line {line}: {message}. Trace the value to its origin and decide what should happen when it is absent.",
    },
    "RUNTIME_ZERO_DIVISION": {
        1: "Line {line} divides by zero. Add a check for the divisor before dividing.",
        2: "The divisor on line {line} was 0. Think about which inputs can make it zero and handle that case before the division.",
        3: "Zero division on line {line}: {message}. Guard the operation: only divide when the divisor is non-zero.",
    },
    "RUNTIME_RECURSION": {
        1: "The recursion on line {line} never stops. Make sure the base case is reachable.",
        2: "A recursive call from line {line} exceeded the depth limit. Check that the base case exists, is correct, and is reached for every path.",
        3: "Recursion error at line {line}: {message}. Trace one call by hand: does the argument actually move toward the base case each step?",
    },
    "RUNTIME_TIMEOUT": {
        1: "The code ran too long and was stopped. Look for a loop that may never finish on line {line} or earlier.",
        2: "Execution timed out. Check loop conditions on line {line} — something is probably not making progress toward termination.",
        3: "Timeout: {message}. The loop guard near line {line} never becomes false under these inputs; dry-run the loop with a tiny input.",
    },
    "RUNTIME_MEMORY": {
        1: "The code used more memory than allowed. Look for building a huge list or string on line {line}.",
        2: "Memory limit exceeded. Line {line} likely accumulates unbounded data — consider generating values lazily instead of storing them all.",
        3: "Memory error near line {line}: {message}. Estimate how much data your algorithm holds at once; it grows too fast for the limit.",
    },
    "RUNTIME_OTHER": {
        1: "The program crashed with an error on line {line}. Read the message — Python usually names the exact problem.",
        2: "An uncaught exception surfaced on line {line}. Follow the traceback from the bottom up to find the first line of your code.",
        3: "Runtime error on line {line}: {message}. Reproduce it with a minimal input and inspect each value involved.",
    },
    # --- Logic ---
    "LOGIC_WRONG_OUTPUT": {
        1: "The program runs but the result on line {line} differs from what the test expects. Re-read the requirement once more.",
        2: "Output mismatch: the value produced where line {line} contributes isn't what the tests expect. Try the smallest failing example by hand.",
        3: "Wrong output: {message}. Compare your expected intermediate values against actual ones around line {line} — the divergence point is the bug.",
    },
    "LOGIC_SUSPICION": {
        1: "Something around line {line} looks logically off. Consider the edge cases: empty input, one element, duplicates.",
        2: "There may be a logic issue near line {line}. Ask: what happens with empty input, a single element, or negative numbers?",
        3: "Possible logic issue at line {line}: {message}. Construct a concrete input where this path gives the wrong answer.",
    },
    # --- Quality ---
    "QUALITY_UNUSED": {
        1: "The name on line {line} is created but never used. It can usually be removed.",
        2: "Line {line} defines something unused. Removing dead code keeps the program honest; if it was meant to be used, that's a different bug.",
        3: "Unused: {message} at line {line}. Either delete it or wire it in — an unused import or variable often hides a forgotten step.",
    },
    "QUALITY_STYLE": {
        1: "A style convention is broken on line {line}. It won't stop the program, but clean style helps you spot real bugs.",
        2: "Style issue at line {line}: {message}. Follow the convention so the important differences stand out.",
        3: "Style: {message} on line {line}. Fix the formatting — consistent style makes future errors easier to see.",
    },
    "QUALITY_COMPLEXITY": {
        1: "This block is deeply nested, which hides bugs. Consider flattening it with early returns.",
        2: "High nesting around line {line} makes the logic hard to follow. Guard clauses or breaking out a helper function would flatten it.",
        3: "Complexity: {message} near line {line}. Each nesting level multiplies the states you must reason about; reduce them.",
    },
    # --- Performance ---
    "PERF_NESTED_LOOP": {
        1: "Nested loops around line {line} may be slow on large inputs. Consider whether a set or dict lookup could replace the inner loop.",
        2: "The nested loops at line {line} look quadratic. For big inputs, hash-based lookups (set/dict) usually beat an inner scan.",
        3: "Performance: {message} at line {line}. If the input can be large, restructure so each element is visited once.",
    },
    "PERF_REPEATED_WORK": {
        1: "The same work is repeated inside a loop near line {line}. Compute it once before the loop.",
        2: "Line {line} recomputes something loop-invariant. Hoist it out of the loop, or remember results you already computed.",
        3: "Repeated work near line {line}: {message}. Cache the value or move the computation outside the loop.",
    },
    # --- Environment ---
    "ENV_UNSUPPORTED": {
        1: "This environment doesn't support that feature or package (line {line}).",
        2: "Line {line} uses something the sandbox doesn't provide. Standard library only — restructure using built-ins.",
        3: "Unsupported: {message} at line {line}. Rewrite using the Python standard library.",
    },
}


# Generic templates: used when a diagnostic carries a category we do not
# recognise (for example a legacy or tool-specific name). The mentor must
# never crash on an unknown category — it degrades to a safe, vaguer hint.
_GENERIC: dict[int, str] = {
    1: "Something near line {line} doesn't look right. Read that line and the one above it once more.",
    2: "Analysis flagged an issue around line {line}. Compare that line with a similar one you know works.",
    3: "Issue near line {line}: {message}. Trace the values involved and check the surrounding lines.",
}

# Aliases for category names that are not taxonomy values (legacy analyzer
# output, tool rule names, or OCR-derived labels).
CATEGORY_ALIASES: dict[str, str] = {
    "line_length": Category.QUALITY_STYLE.value,
    "documentation": Category.QUALITY_STYLE.value,
    "style": Category.QUALITY_STYLE.value,
    "pep8": Category.QUALITY_STYLE.value,
    "pep8_naming": Category.QUALITY_STYLE.value,
    "naming": Category.QUALITY_STYLE.value,
    "syntax_error": Category.SYNTAX_UNEXPECTED_TOKEN.value,
    "syntax": Category.SYNTAX_UNEXPECTED_TOKEN.value,
    "indentation": Category.SYNTAX_INDENTATION.value,
    "undefined_variable": Category.NAME_UNDEFINED.value,
    "undefined_name": Category.NAME_UNDEFINED.value,
    "unused_import": Category.QUALITY_UNUSED.value,
    "unused_variable": Category.QUALITY_UNUSED.value,
    "performance": Category.PERF_NESTED_LOOP.value,
    "complexity": Category.QUALITY_COMPLEXITY.value,
    "unsupported_language": Category.ENV_UNSUPPORTED.value,
    "unsupported": Category.ENV_UNSUPPORTED.value,
    "demo": Category.RUNTIME_OTHER.value,
}


def resolve_category(category: str) -> str | None:
    """Map an incoming category name to a known template key, if possible."""
    if category in _TEMPLATES:
        return category
    return CATEGORY_ALIASES.get(category) or CATEGORY_ALIASES.get(category.lower())


def fallback_hint(category: str, level: int, message: str, line: int, rule: str = "") -> str:
    """Build a template hint.

    Never raises: an unrecognised category degrades to a generic template, so
    the mentor always has something safe to say (H1-H3 only, no code).
    """
    resolved = resolve_category(category)
    level_templates = _TEMPLATES.get(resolved) if resolved else None
    if level_templates:
        template = level_templates.get(level) or level_templates[1]
    else:
        template = _GENERIC.get(level) or _GENERIC[1]
    return template.format(message=message, line=line, rule=rule or (resolved or category).lower())


def has_template_for(category: str, level: int) -> bool:
    """True if a specific template exists for this category at this level."""
    resolved = resolve_category(category)
    return bool(resolved and _TEMPLATES.get(resolved, {}).get(level))
