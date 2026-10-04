# 11 — Final Checklist

Tick items only with evidence (command output, test report, ADR). Update this file at every phase exit.

## A. Planning stage (this bundle)

- [x] Abstract and technology list reviewed; verdicts recorded (`01-STACK-AND-ABSTRACT-REVIEW.md`)
- [x] Requirements with IDs, priorities, gates and phases (`02-REQUIREMENTS.md`)
- [x] Architecture, contracts, data model, safety design (`03-ARCHITECTURE.md`)
- [x] Folder structure and file manifest (`04-FOLDER-STRUCTURE.md`)
- [x] Phased plan with verification, exit criteria and rollback (`05-IMPLEMENTATION-PLAN.md`)
- [x] Dependencies, environment variables and commands (`06-DEPENDENCIES-AND-COMMANDS.md`)
- [x] Test plan and traceability matrix (`07-TESTING-AND-VALIDATION.md`)
- [x] Rollback and failure handling (`08-ROLLBACK-AND-FAILURE-HANDLING.md`)
- [x] Risk register and edge cases (`09-RISKS-AND-EDGE-CASES.md`)
- [x] Open questions with options and provisional defaults (`10-OPEN-QUESTIONS.md`)
- [x] Four planning review cycles completed (`12-REVIEW-LOG.md`)
- [x] Q1 decided: both editor and screen source, automatic code-region discovery/tracking by default
- [ ] Q2–Q7 answered by you
- [ ] You said "start Phase 0"

## B. Phase exits

### PH0 — Decisions and scaffold
- [ ] ADRs for Q1–Q7 written
- [ ] Tool versions printed and pinned
- [ ] `make check` green locally and in CI
- [ ] Database container healthy
- [ ] No product code exists

### PH1 — Walking skeleton
- [ ] Contract v0 frozen in an ADR; generated types up to date
- [ ] Placeholder marker appears from typing; stale results never applied
- [ ] Reconnect and resync work; disallowed Origin rejected
- [ ] Logs carry stage timings and no code

### PH2 — Fast static analysis
- [ ] Tree-sitter, Python parser and Ruff results mapped to the taxonomy
- [ ] Analyzer timeouts and crashes handled
- [ ] Baseline analysis eval and latency benchmark recorded with sample sizes
- [ ] You were asked for quality targets (SC-2, Q14)

### PH3 — Sandbox and execution
- [ ] Every isolation and limit test passes on Linux with Docker
- [ ] API container has no Docker socket
- [ ] Runtime and test diagnostics point at the right lines; hidden tests never leak
- [ ] `EXECUTION_ENABLED=false` verified

### PH4 — Mentor engine
- [ ] Model chosen by bake-off, recorded in an ADR
- [ ] Adversarial suite passes; no fenced code at H1–H3
- [ ] Template-only mode verified with `LLM_ENABLED=false`
- [ ] Floating mentor overlay passes keyboard, dismissal, stale-state and safe-placement tests
- [ ] Scenarios S1–S6 pass; mentor latency reported

### PH5 — Persistence and learner record
- [ ] Migrations upgrade and downgrade; backup and restore tested
- [ ] Record survives a restart; database-stopped drill passes
- [ ] No raw frames and no code content in logs or database by default (SC-6)
- [ ] Identity mode implemented as decided in Q5

### PH6 — Analytics, quality checks, adaptation
- [ ] Dashboard equals direct SQL (SC-7)
- [ ] Adaptation rules tested; switch verified
- [ ] Quality analyzers evaluated against clean negatives

### PH7 — Screen source and OCR
- [ ] Capture feasibility, automatic code-discovery evaluation and OCR bake-off recorded in ADRs
- [ ] Automatic code region is detected and tracked across movement/resize cases
- [ ] Low-confidence region path yields no diagnostics and offers manual fallback
- [ ] Consent flow, indicator, pause, stop and manual override tested
- [ ] Floating mentor follows detected region and never obscures active code beyond P-17
- [ ] No frames persisted; `FEATURE_SCREEN_SOURCE` defaults to false; `AUTO_CODE_DISCOVERY_ENABLED` can be disabled

### PH8 — Additional languages
- [ ] Each added language: grammar, linter, image, templates, corpus
- [ ] Isolation suite passes on each new image
- [ ] Baseline eval recorded per language

### PH9 — Hardening, evaluation, release
- [ ] Latency benchmark against P-02 and mentor latency recorded
- [ ] Security review done against the table in `03-ARCHITECTURE.md` section 10
- [ ] Accessibility pass done
- [ ] Clean-checkout rehearsal using only the documented commands
- [ ] Evidence attached for SC-1 to SC-8

## C. Release checklist

**Quality** — all P0 requirements have a passing test (matrix in `07`); CI green; scenarios in scope pass.
**Security** — sandbox suite passes; Origin and size checks tested; no Docker socket in the API; dependency audit and secret scan clean; each kill switch tested.
**Privacy** — no frames, no code in logs; consent and disclosure visible; retention and delete-my-data tested; redaction before LLM calls and before stored code text.
**Operations** — backup and restore rehearsed; rollback rehearsed from the latest tag; `.env.example` complete.
**Documentation** — README accurate; ADRs complete; demo script written; limitations stated.

## D. Limitations to state in the final report

- Logic errors are detected only where a test or expected output exists; otherwise they are labelled suspicions.
- Screen mode depends on a readable and correctly discovered code region; low-confidence region or OCR states produce a notice/manual fallback, not a guess.
- Hints are guard-railed and measured, not guaranteed correct.
- Only the languages chosen in Q2 are supported; learner code is limited to the standard library unless Q11 says otherwise.
- Single-file programs only.
- Quality numbers come from the evaluation dataset at the sample sizes reported.
