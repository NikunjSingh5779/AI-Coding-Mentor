# 10 — Open Questions

You asked me to ask rather than assume. These are the things the plan cannot decide for you. **Q2–Q7 have been resolved** as documented in ADR-0002. Q1 was decided previously. Q8–Q14 are smaller; each has a provisional default so the plan stays concrete, and you only need to reply if you disagree. D1–D10 are low-impact tooling defaults.

**How to answer:** reply with the question number and a letter or your own words, for example `Q2 A, Q3 B, Q4 C, Q5 A, Q6 <your dates, team, evaluation>, Q7 A`. Replying `defaults` accepts the recommendation for Q1–Q5 (marked ★); Q6 and Q7 still need your own words because only you know them. Each answer becomes an ADR in PH0.

## Blocking questions

### Q1 — How does the system get the learner's code? — **DECIDED**

**Decision:** Both editor input and screen capture are in scope. Build the editor path first and screen mode second. In screen mode, the normal workflow is automatic code-region discovery and tracking; manual region selection is a fallback when confidence is low or the learner overrides it. The floating mentor can be used in both editor and screen modes.

**Why it matters:** The editor source reads code exactly. The screen source adds capture, change detection, automatic code discovery, tracking, OCR and confidence gating, and is the biggest source of false errors.

- A. In-browser code editor only
- B. Screen capture and OCR only
- C. **Both: editor first, screen second, with automatic code-region discovery by default** ★ **SELECTED**
- D. VS Code extension (not web-based), alone or alongside A

**Recorded behavior:**
- Automatic code discovery is the normal screen workflow.
- Manual region selection is retained only as a fallback/override.
- Low-confidence detection never produces diagnostics.
- The selected region is tracked as the editor moves or resizes.
- The floating mentor is positioned using detected region geometry and must not obscure the active code beyond the configured threshold.

**What changes:** FR-02, FR-19, FR-20, FR-27, FR-28; `03-ARCHITECTURE.md`; PH4, PH7; the `vision/`, capture and mentor overlay files.

### Q2 — Which learner languages must the first release support? — **RESOLVED**

**Decision:** A - Python only for first release

**Why it matters:** Each language needs a grammar, a linter wrapper, a sandbox image, taxonomy mappings, a test corpus and fallback templates. TypeScript is the app's own language, not a learner language, unless you say otherwise (then ESLint returns for learner code).

- A. Python only ★ **SELECTED**
- B. Python and C++
- C. Python and Java
- D. Python, C++ and Java
- E. Others (name them)

**Recorded behavior:**
- Focus on Python ecosystem for MVP delivery
- Excellent tooling support (AST parsing, linting, testing)
- Additional languages can be added in Phase 8
**What changes:** FR-04 to FR-06, FR-24; PH2, PH3, PH8; the C++ and Java files in the manifest.

### Q3 — What tells the system what the code is supposed to do? — **RESOLVED**

**Decision:** B - Built-in problem bank with test cases

**Why it matters:** A logic error is wrong behaviour relative to an intent. Without test cases or expected outputs, the system can find syntax, runtime and style problems exactly, but logic problems only as unverified suspicions.

- A. Nothing: free-form coding; logic findings are suspicions only
- B. A built-in problem bank with test cases (you say how many; I can draft seed problems for you to review) ★ **SELECTED**
- C. The learner pastes a problem statement, optionally with sample input and output (tests are those samples only)
- D. B and C together

**Recorded behavior:**
- Built-in problem bank enables verified logic error detection
- Start with small seed set of 5-10 problems
- Free-form coding remains available as fallback
**What changes:** FR-07, FR-22; PH3; `problems/`, `api/problems.py`, the test-results panel.

### Q4 — Which LLM will the mentor use? — **RESOLVED**

**Decision:** C - Both local and hosted, switchable

**Why it matters:** With a hosted API, learner code leaves the machine (disclosure and redaction apply) and cost needs controlling. With a local model, latency depends on your GPU memory and the model's size.

- A. Local only (LM Studio)
- B. Hosted API only (which provider, and is there a budget?)
- C. Both, switchable ★ **SELECTED**

**Recorded behavior:**
- Adapter pattern handles both local (LM Studio) and hosted APIs
- Phase 4 bake-off will pick default from available models
- Flexible deployment for privacy/cost/performance tradeoffs
**What changes:** FR-14, NFR-02, NFR-04, NFR-11; PH4; environment variables.

### Q5 — Who will use it, and where does it run? — **RESOLVED**

**Decision:** A - Single user on local machine

**Why it matters:** Serving other people needs authentication, per-user quotas, TLS, stronger sandbox isolation and a privacy review. Running on your own machine does not.

- A. Single user on your machine: demo, viva or personal use ★ **SELECTED**
- B. Hosted for several learners with accounts

**Recorded behavior:**
- Single-user deployment simplifies security model for MVP
- Every record carries `user_id` for future multi-user upgrade
- No authentication, quotas, or TLS required initially
**What changes:** FR-21, NFR-03, NFR-09; PH3, PH5, PH9; `core/security.py`.

### Q6 — Deadline, team and evaluation — **RESOLVED**

**Decision:** 2-week prototype timeline with solo development and portfolio demonstration

**Why it matters:** Without it I cannot map phases to a calendar or decide what to cut. The plan contains no dates for that reason.

**Recorded behavior:**
- **Timeline**: 2-week prototype development
- **Team**: Solo development, 10-15 hours per week
- **Evaluation**: Portfolio demonstration with live coding session
- **Scope**: Focused on core MVP functionality (PH0-PH5)
**What changes:** the timeline in `05-IMPLEMENTATION-PLAN.md`, the cut order, PH9 content.

### Q7 — What already exists? — **RESOLVED**

**Decision:** A - Start from current planning repository

**Why it matters:** The rules say to prefer existing components over rebuilding. I cannot do that without knowing what exists.

- A. Nothing: start from an empty repository ★ **SELECTED**
- B. Something exists (repository, prototype, dataset, accounts). Describe it, and say whether to reuse anything from your other work. Please do not paste secrets.

**Recorded behavior:**
- Clean slate development from current planning foundation
- Solid architectural planning documents already established
- No legacy constraints or existing codebase to integrate
**What changes:** CURRENT STATE in `00-PROJECT-BRIEF.md`; PH0-S1 (re-scope).

## Non-blocking questions (provisional defaults; reply only to change them)

### Q8 — In which language and at what reading level should explanations be written?
Default: English, plain language for a beginner; templates are structured so other languages can be added later. Affects FR-10 and the fallback templates.

### Q9 — What should "improvement" mean on the dashboard?
Default: the metric set M1 to M6 in `03-ARCHITECTURE.md` section 11. Affects FR-17 and PH6.

### Q10 — What code may be stored, and for how long?
Default: store diagnostics, issue metadata and hint text; store code text only at checkpoints, with secrets redacted; keep records until the learner deletes them, with a delete-my-data function; no automatic expiry (`RETENTION_DAYS` unset). Affects FR-15, NFR-04, PH5.

### Q11 — Which language versions and packages may learner code use?
Default: standard library only; interpreter and compiler versions are the current stable releases that the sandbox images support at PH3, printed and recorded in an ADR. Affects PH2, PH3, PH8 and the ENV_UNSUPPORTED category.

### Q12 — Where should the database run?
Default: PostgreSQL in Docker with standard drivers; Supabase-hosted PostgreSQL stays possible later (decide together with Q5). Affects D6 and PH5.

### Q13 — Do you approve the hint ladder and the rule for revealing the fix?
Default: H1 to H4 as in `03-ARCHITECTURE.md` section 8.2; H4 only on explicit request after H3 has been shown and a confirmation click; no automatic escalation. Alternatives: allow H4 after a number of failed attempts, or add an instructor setting that disables H4. Affects FR-11.

### Q14 — Do you have required response times?
Default: the P-02 target for markers; the mentor target is set after the PH4 bake-off. Tell me if your evaluation states a required response time. Affects NFR-01 and NFR-02.

## Tooling defaults (low impact; veto any at no cost)

| ID | Default | Reason | Cost of changing |
|---|---|---|---|
| D1 | Monorepo with `backend/`, `frontend/`, `sandbox/`, `eval/`, `docs/` | Separate toolchains and trust levels in one place | Low before PH1 |
| D2 | Python tooling: uv, Ruff, pytest with pytest-asyncio, one type checker (pyright or mypy) | Fast and common | Low |
| D3 | Frontend tooling: Vite, pnpm, Vitest, Testing Library, Playwright; ESLint and Prettier for our own code | Common and fast | Low |
| D4 | Monaco through `@monaco-editor/react`, bundled locally | Works offline and under a strict content-security policy | Low |
| D5 | React Router and Zustand | Small and enough for session and settings state | Low |
| D6 | SQLAlchemy 2 async, asyncpg, Alembic | Standard async stack with migrations | Medium after PH5 |
| D7 | Contracts from Pydantic to JSON Schema to TypeScript, checked in CI | One source of truth | Low |
| D8 | GitHub Actions with backend, frontend, contracts and sandbox jobs | You use GitHub | Low |
| D9 | Makefile as the task runner; plain commands always documented | One entry point; native Windows needs WSL or the plain commands | Low |
| D10 | Structured JSON logging with correlation IDs | Needed for latency tuning | Low |

## Decision log

| Question | Answer | Date | Recorded in |
|---|---|---|---|
| Q1 | DECIDED — C with automatic code discovery and tracking | 2026-10-04 | `docs/adr/0001-screen-source-and-auto-code-discovery.md` |
| Q2 | DECIDED — A: Python only | 2026-10-04 | `docs/adr/0002-blocking-questions-resolved.md` |
| Q3 | DECIDED — B: Built-in problem bank | 2026-10-04 | `docs/adr/0002-blocking-questions-resolved.md` |
| Q4 | DECIDED — C: Both local and hosted | 2026-10-04 | `docs/adr/0002-blocking-questions-resolved.md` |
| Q5 | DECIDED — A: Single user local | 2026-10-04 | `docs/adr/0002-blocking-questions-resolved.md` |
| Q6 | DECIDED — 2-week prototype, solo dev | 2026-10-04 | `docs/adr/0002-blocking-questions-resolved.md` |
| Q7 | DECIDED — A: Start from current repo | 2026-10-04 | `docs/adr/0002-blocking-questions-resolved.md` |
| Q8 to Q14 | ACCEPTED — Provisional defaults | 2026-10-04 | `docs/adr/0003-consolidated-project-decisions.md` |
