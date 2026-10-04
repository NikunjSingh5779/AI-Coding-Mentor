# 12 — Review Log

You asked for the plan to be reviewed three times in a cycle. This file records what each cycle checked, what it found and what changed. Every finding below was present in the draft that preceded it and is fixed in the files you have now.

**Method.** Draft v1 was written as 14 files. Each cycle then used a different lens, ran automated checks, did a manual read-through, fixed what it found, and re-ran every earlier check. The three lenses were chosen so that each cycle can catch what the others cannot: completeness and validity, then truthfulness and consistency, then whether a coding agent can actually execute the plan.

**The checkers were themselves tested.** The main validator was run against a copy with five deliberate defects injected (a wrong phase for a requirement, a path missing from the manifest, a missing question definition, a deleted traceability row, a broken import in `CLAUDE.md`). It raised seven errors and caught all of them. The diagram parser was shown a deliberately broken diagram and rejected it.

## What the automated checks cover

| Check | What it verifies |
|---|---|
| Structure validator | All 14 files exist; no placeholders; links and `@` imports resolve; every requirement ID appears in the traceability matrix and every phase's Covers line matches `02-REQUIREMENTS.md`; every question, default, parameter, risk and success-criterion ID that is mentioned is defined; every repository path mentioned in the docs exists in the file manifest; diagram blocks and code fences are well formed |
| Template and stack coverage | All 41 labels of your template appear in order in `00-PROJECT-BRIEF.md`; all 30 items of your technology list have a verdict in `01-STACK-AND-ABSTRACT-REVIEW.md`; every abstract statement points at a requirement, question, parameter or default |
| Consistency | Every environment variable and WebSocket message type used anywhere is defined once; every count stated in prose (D1–D10, P-01 to P-15, S1–S11, SC-1 to SC-8, M1 to M6, Q1–Q14, ten phases) matches the real count; every "section N" reference points at an existing heading |
| Executability | Every file a phase creates is named in one of that phase's steps; every table row has the same number of cells as its header |
| Diagrams | All five Mermaid diagrams pass the real Mermaid parser |
| Reader test | Twelve questions a newcomer would ask are each answered where the docs say they are |

## Cycle 1 — Completeness and validity

**Lens:** does every part of your request and template have content, and is each claim valid?
**Automated result before fixes:** structure validator 0 errors; template, stack and abstract coverage 0 gaps.
**Manual read-through found these gaps, all fixed:**

| # | Finding | Fix |
|---|---|---|
| 1.1 | The abstract promises "a record of the learner's coding mistakes", but the only learner-facing view was the P1 dashboard, so the record was invisible in P0 | Added `frontend/src/routes/history.tsx` in PH5; FR-16, PH5-S4 and the test matrix updated |
| 1.2 | No interface to pick a problem or read its statement, although problems and test cases were planned | Added `frontend/src/features/problems/ProblemPanel.tsx` (PH3, gated by Q3); PH3-S7 and tests updated |
| 1.3 | In screen mode the learner's own editor cannot be annotated, so there was nowhere to show markers | Added a read-back view of the reconstructed code with markers (`03-ARCHITECTURE.md` section 4.3, FR-20, PH7-S4, tests); it also makes OCR misreads visible |
| 1.4 | The `issue.dismiss` message had no requirement behind it | Added to FR-13 and its tests |
| 1.5 | No rule for a hint that arrives after the learner has already changed the code | Added to FR-13, the trigger table (`03-ARCHITECTURE.md` section 8.1), PH4-S6 and tests |
| 1.6 | Prompt size was unbounded, which breaks small local context windows | Added a token-budget rule (`03-ARCHITECTURE.md` section 8.4) and the `LLM_CONTEXT_TOKENS` setting |
| 1.7 | Requirement-to-phase tables understated where work really happens: Origin and size limits are built in PH1, privacy storage in PH5, failure drills in PH2, PH3 and PH7, the runner service in PH3 | Corrected NFR-04, NFR-05, NFR-08 and NFR-09 in `02-REQUIREMENTS.md`, the Covers lines in `05-IMPLEMENTATION-PLAN.md`, the Origin row in `01`, and added the compose step to PH3 |
| 1.8 | A hardware figure was repeated in the architecture doc, creating a second place to keep in sync | Replaced with a pointer to the single statement in `00-PROJECT-BRIEF.md` |

**After:** validator 0 errors; two warnings that are expected (P-05 and P-06 are used only inside the architecture document).

## Cycle 2 — Truthfulness, assumptions and consistency

**Lens:** is anything invented or silently assumed, are all numbers and choices tagged, and do the files agree with each other?
**Manual findings, all fixed:**

| # | Finding | Fix |
|---|---|---|
| 2.1 | Redaction of secrets before storing code text was stated in three files but missing from `CLAUDE.md`, the requirements, the architecture (principles, data model, security table), the layering rules, PH5 and the test matrix | Aligned all of them; the learner service may now use the redaction module, and a stored-text test was added |
| 2.2 | Four references of the form "see section N" in the plan did not name the document, so they could be read as pointing into the plan itself | Named the document in each; also in the manifest text |
| 2.3 | Assumptions about you were stated as fact: "your institution", a team of "just you with coding agents", LM Studio "already in your setup", a software list without "confirm", a hardware figure used as a constraint | Reworded neutrally, added "(confirm)", made the hardware constraint conditional on Q4 |
| 2.4 | The LM Studio instructions were cross-referenced to the wrong section | Corrected |
| 2.5 | `CLAUDE.md` said never log code "at INFO level or above" while the requirements say never in logs | Made consistent: never log code, OCR text or prompts |

**Automated:** every environment variable and message type is defined once; all prose counts match; the section-reference check initially flagged four references, all fixed; its last flag was a formatting artefact in a manifest string, fixed at the start of cycle 3.

## Cycle 3 — Executability and safety

**Lens:** can a coding agent execute one phase without guessing, and is every hard safety rule enforced by something automatic?
**Findings, all fixed:**

| # | Finding | Fix |
|---|---|---|
| 3.1 | Two rules contradicted each other in practice: "touch only the listed files" versus unavoidable wiring edits (registering routers, extending compose and CI) | Added an explicit exception to `CLAUDE.md` and to the plan's rules: minimal wiring changes to earlier files are allowed and must be reported |
| 3.2 | The hard safety rules (import layering, never execute learner text in the API) had no automatic enforcement | Added `test_architecture_rules` to PH1-S6, the unit-test list and the NFR-03 and NFR-07 matrix rows |
| 3.3 | The kill switches and settings were defined in `06` but not named in the steps that use them | Named them in the PH1 to PH8 steps, so wiring configuration needs no guessing |
| 3.4 | `backend/app/__init__.py` was created in PH1 but named in no step (found by the file-to-step check) | Named in PH1-S2 |
| 3.5 | The note about other coding agents was vaguer than the documentation it relies on | Reworded to match: Claude Code reads `CLAUDE.md`, not `AGENTS.md` |
| 3.6 | The tree, manifest and per-phase file lists are generated for this bundle but are plain text once delivered | `04-FOLDER-STRUCTURE.md` now says to update all three together, and PH0-S1/S2 does so |
| 3.7 | Reader test: one of twelve questions had no answer — what happens to the plan if you choose "screen only" for Q1 | Added the "If B" consequence to Q1 and to PH1, plus a general rule that gated files and steps are built only if the recorded answer needs them (PH0-S2 lists them) |

**Automated:** the file-to-step check found one gap (3.4, fixed); table structure 0 problems; all five diagrams parse; the reader test now answers 12 of 12.

## Cycle 4 — Automatic code discovery and floating mentor review

**Lens:** does the clarified screen workflow actually describe automatic code discovery, tracking and a floating mentor without weakening the existing OCR, privacy, safety and verification rules?

**Changes made:**

| # | Finding | Fix |
|---|---|---|
| 4.1 | Screen mode still treated manual region selection as the normal path | Changed Q1 and PH7 so automatic code-region discovery is the default and manual selection is fallback/override |
| 4.2 | No explicit abstraction for detecting or tracking the code region | Added `code_region_detect.py`, `region_tracking.py`, `CodeRegion`, `region.update`, P-16 and dedicated evaluation data |
| 4.3 | No dedicated floating mentor presentation layer | Added `FloatingMentor.tsx`, `overlayPosition.ts`, FR-28, placement/stale-state tests and P-17 |
| 4.4 | Testing covered OCR but not wrong-region selection or movement | Added S9–S11, region evaluation metrics, movement/reacquisition tests and risk R-17/R-18 |
| 4.5 | Planning status and decision log still treated Q1 as open | Recorded Q1 as decided and left Q2–Q7 blocking |

**Validation:** cross-file references were updated for the new requirement IDs, files, phase steps, parameters, kill switches, risks, acceptance scenarios and checklist items. No product code or dependency installation was performed.

## Final state

| Item | Value |
|---|---|
| Files in the bundle | `CLAUDE.md` plus 13 documents and one Q1 ADR (updated planning bundle) |
| Requirements | 39 (28 functional, 11 non-functional), every one in the traceability matrix |
| Repository paths in the manifest | 155, grouped by phase and gate |
| Phases | 10 (PH0 to PH9), plus a backlog with pull-in triggers |
| Risks, scenarios, parameters | 18, 11 and 17 |
| Questions | 6 blocking (Q2–Q7), 8 entries including the decided Q1 and 7 non-blocking with provisional defaults, 10 tooling defaults |
| Final check run | 0 errors; 2 expected warnings |

## What these reviews do not prove

- They prove the documents agree with each other and are executable as written, **not** that the design is right. Three cycles by one author share blind spots; your own read of `10-OPEN-QUESTIONS.md` and `01-STACK-AND-ABSTRACT-REVIEW.md` is the review that matters most.
- Nothing has been built or run, so no command in `06` was executed, no dependency version was checked, and no latency, OCR or hint-quality claim has been measured. Those are exactly what the phase verifications and evaluations are for.
- The diagram check is syntax only, not rendering.
- Checked against current documentation during this work: the `@` import syntax and the `AGENTS.md` behaviour of Claude Code's `CLAUDE.md`, and LM Studio's OpenAI-compatible endpoints and default address. Everything else that depends on a tool's current behaviour is marked indicative and must be verified when it is run: the Monaco loader default, Tailwind, shadcn/ui, uv and pnpm commands, Docker flags, Tree-sitter binding APIs, OCR engine behaviour and background-tab sampling.
- The ratings in `09-RISKS-AND-EDGE-CASES.md` are my estimates, and every number in `03-ARCHITECTURE.md` section 12 is a provisional starting point, not a decision.
