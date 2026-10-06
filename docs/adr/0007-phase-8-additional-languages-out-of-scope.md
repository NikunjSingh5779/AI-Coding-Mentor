# ADR-0007 — Phase 8 (additional languages) is out of scope for this release

- **Status:** Accepted
- **Date:** 2026-10-06
- **Phase:** PH8
- **Deciders:** Project owner (Q2)

## Context

PH8 in `docs/05-IMPLEMENTATION-PLAN.md` adds each language chosen in Q2 to the
same standard as Python. Its only file deliverables are gated on Q2:

- `backend/app/analysis/linters/cpp.py` — *only if Q2 includes C++* [gate Q2]
- `backend/app/analysis/linters/java.py` — *only if Q2 includes Java* [gate Q2]
- `sandbox/images/cpp/Dockerfile` — *only if Q2 includes C++* [gate Q2]
- `sandbox/images/java/Dockerfile` — *only if Q2 includes Java* [gate Q2]

The gated steps PH8-S1…S4 (grammar + linter, sandbox image, mentor templates,
corpus/eval per language) are likewise conditional.

## Decision

**No additional languages are added.** Q2 was resolved as **A — Python only**
(`docs/10-OPEN-QUESTIONS.md`, `docs/adr/0002-blocking-questions-resolved.md`).

The PH8 rule "a file or step tagged with a gate is built only if the recorded
answer needs it" therefore makes every PH8 deliverable a no-op. Building C++
or Java tooling would contradict the recorded decision and add code the
project does not run, test, or document.

## Consequences

- No `analysis/linters/cpp.py`, `analysis/linters/java.py`,
  `sandbox/images/cpp/`, or `sandbox/images/java/` are created.
- `ENABLED_LANGUAGES` stays `["python"]`.
- The existing single-language paths (Tree-sitter Python, Python AST, Ruff,
  the Python sandbox image, and the per-category fallback templates) already
  satisfy FR-24 for the languages in scope.
- Re-opening this decision requires a new ADR and an updated Q2 — the
  architecture (grammar registry, linter interface, sandbox language
  templates, taxonomy mapping) is already language-pluggable, so adding a
  language later is additive, not a rewrite.

## Verification

- `backend/app/analysis/treesitter/parser.py` registers only `python`.
- `backend/app/vision/language_detect.py` tests only registered grammars and
  falls back to `python`.
- No C++/Java artifacts exist in the repository (`sandbox/images/` contains
  only `python/`).
