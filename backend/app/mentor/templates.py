TEMPLATES = {
    "SYNTAX_MISSING_TOKEN": {
        1: "Inspect the highlighted punctuation or delimiter.",
        2: "Compare the highlighted statement with the surrounding syntax.",
        3: "Check the matching delimiter or block terminator, then verify indentation.",
        4: "Correct the missing delimiter or block terminator reported by the parser.",
    },
    "SYNTAX_INDENTATION": {
        1: "Inspect the indentation of the highlighted line.",
        2: "Align the highlighted statement with the block that contains it.",
        3: "Check for mixed indentation across this block.",
        4: "Normalize the highlighted block indentation.",
    },
    "NAME_UNDEFINED": {
        1: "Check whether the highlighted name is defined before this line.",
        2: "Check the spelling and scope of the identifier.",
        3: "Trace where the value should be created or imported.",
        4: "Define or correctly reference the missing identifier before use.",
    },
    "QUALITY_UNUSED": {
        1: "Check whether the highlighted import or variable is used.",
        2: "Remove it or make sure the current implementation needs it.",
        3: "Unused names can indicate unfinished logic; inspect the surrounding block.",
        4: "Remove the unused item if it has no purpose.",
    },
    "QUALITY_STYLE": {
        1: "Inspect the highlighted style warning.",
        2: "Make the smallest style correction that preserves behavior.",
        3: "Apply the linter convention consistently in this block.",
        4: "Apply the exact style correction reported by the linter.",
    },
    "LOGIC_SUSPICION": {
        1: "Trace the highlighted branch with one simple input.",
        2: "Check the boundary case represented by this branch.",
        3: "Walk through the state changes line by line against the requirement.",
        4: "Adjust the branch so its state transition matches the requirement.",
    },
}

def template_hint(category: str, level: int) -> str:
    levels = TEMPLATES.get(category, TEMPLATES["LOGIC_SUSPICION"])
    return levels.get(level, levels[max(levels)])
