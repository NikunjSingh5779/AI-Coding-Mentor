# CLAUDE.md — AI Real-Time Coding Screener / AI Coding Mentor

> **STATUS: PLANNING ONLY. Nothing is built.** Do not create product code, install dependencies or scaffold folders until the remaining blocking questions Q2–Q7 in `docs/10-OPEN-QUESTIONS.md` are answered and the user explicitly says "start Phase N". Q1 is now decided: both editor input and screen capture are in scope, with automatic code-region discovery and tracking in screen mode and manual region selection only as a fallback. Planning documents may be edited when decisions arrive.

## What this is

A web app that watches a learner's code as it is written, finds syntax, runtime, logic and quality problems with real tools (parsers, linters, sandboxed execution, test cases), and uses an LLM to turn those *verified* findings into progressive hints. It never gives the full solution unless the learner explicitly asks at the last hint level. It records mistakes and progress per learner.

The filled project brief (goal, scope, constraints, priorities, success criteria) is imported here:

@docs/00-PROJECT-BRIEF.md

## Read on demand (not imported, to keep this file small)

**ICM Layer Navigation (Infrastructure-Component-Module)**
- `docs/ICM-INDEX.md` — complete documentation catalog and navigation guide
- `docs/ICM-ROUTING.md` — quick access paths for different developer roles and tasks

**Essential Project Documents**
- `docs/02-STATUS.md` — current project state and what's been built
- `docs/03-ARCHITECTURE.md` — components, flows, contracts, data model, safety design
- `docs/04-FOLDER-STRUCTURE.md` — repo tree, import rules, file manifest per phase
- `docs/05-IMPLEMENTATION-PLAN.md` — phases, steps, verification, exit criteria (read **only the current phase**)

**Full Documentation Suite**
- `docs/00-PROJECT-BRIEF.md` — project goal, scope, constraints, success criteria
- `docs/01-STACK-AND-ABSTRACT-REVIEW.md` — technology stack validation and risk assessment
- `docs/02-REQUIREMENTS.md` — functional and non-functional requirements with priorities
- `docs/06-DEPENDENCIES-AND-COMMANDS.md` — package versions, environment setup, development commands
- `docs/07-TESTING-AND-VALIDATION.md` — test suites, acceptance scenarios, traceability matrix
- `docs/08-ROLLBACK-AND-FAILURE-HANDLING.md` — phase rollback procedures and failure modes
- `docs/09-RISKS-AND-EDGE-CASES.md` — risk register and edge case catalog
- `docs/10-OPEN-QUESTIONS.md` — blocking questions resolved, decision log
- `docs/11-FINAL-CHECKLIST.md` — release readiness and phase-exit checklists
- `docs/12-REVIEW-LOG.md` — review cycles and feedback incorporation
- `docs/adr/` — architecture decision records (ADRs)

## Execution rules (apply to every task)

1. **Do not invent missing information.** Unknown fact, version, number or preference: stop and ask, or write `UNKNOWN` and link the question. Never fill a gap silently.
2. **Do not change unrelated files.** Touch only files listed for the current phase in `docs/04-FOLDER-STRUCTURE.md` and `docs/05-IMPLEMENTATION-PLAN.md`. The one exception: a step may make a minimal wiring change to a file from an earlier phase (for example registering a router in `backend/app/main.py`); list every such change in the phase report. Need any other file? Stop and ask.
3. **Prefer existing components over rebuilding.** Before writing a module, check the libraries in `docs/06-DEPENDENCIES-AND-COMMANDS.md` and the repo for an existing solution.
4. **Verify each major step** with the step's verification command. Report the real output. Never claim a check passed that you did not run.
5. **State uncertainties** in your report: what you could not verify and what you would need to assume (assumptions need the user's approval).
6. **One phase at a time.** Stop at each phase exit and wait for confirmation.
7. **Pin versions from the package registry at scaffold time** and print what you installed. Never copy versions from memory.

## Hard safety rules (never relax)

- Learner code is **untrusted**. It runs only in the sandbox runner (`sandbox/`). Never `exec`, `eval` or spawn learner code in the API process. Never mount the Docker socket into the API container.
- Never persist raw screen frames. Never log code, OCR text or prompts (log hashes and lengths). Redact secrets before any LLM call and before storing code text.
- Hints at levels H1–H3 contain **no** complete solution and no fenced code (enforced in `backend/app/mentor/guardrails.py`). Level H4 only on explicit learner request.
- Learner code, OCR text and automatic code-region detection output are **data, not instructions** inside prompts. The mentor LLM has no tools.
- Never commit `.env` or secrets. Update `.env.example` instead.
- Automatic screen mode must not guess a code region when confidence is below the configured gate; manual region selection is the fallback.

## Phase workflow

Branch `phase/<n>-<slug>`, implement the phase's steps, run the verification, update `docs/05-IMPLEMENTATION-PLAN.md` and `docs/11-FINAL-CHECKLIST.md`, ask the user to confirm, then tag `phase-<n>-complete`. Rollback rules: `docs/08-ROLLBACK-AND-FAILURE-HANDLING.md`.

## Commands (valid only after the Phase 0 scaffold exists)

`make check` · `make test` · `make db-up` · `make dev-backend` · `make dev-frontend` · `make sandbox-build` — each maps to plain commands listed in `docs/06-DEPENDENCIES-AND-COMMANDS.md`, so everything also works without `make`.

## Other coding agents

Claude Code reads `CLAUDE.md`, not `AGENTS.md`. If another agent that reads `AGENTS.md` is used, add an `AGENTS.md` with the same rules or a pointer to this file, and keep one canonical source.
