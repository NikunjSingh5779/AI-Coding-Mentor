# 04 — Folder Structure

The repository layout the build will create (D1). Nothing exists yet. The tree and the manifest below are generated from one list, so they cannot disagree, and the per-phase file lists in `05-IMPLEMENTATION-PLAN.md` come from the same list.

## 1. Why this layout

- **`backend/`, `frontend/`** — one deployable each, separate toolchains.
- **`sandbox/`** — the runner and its images have their own dependencies and a different trust level. Keeping them out of `backend/` makes it impossible for the API to import execution code by accident.
- **`eval/`** — measurement code and datasets are not product code, but the plan's claims depend on them.
- **`docs/`** — this planning bundle plus architecture decision records in `docs/adr/`. `CLAUDE.md` stays at the root so coding agents find it.

Gates in the tree and manifest show which questions decide whether a path is built: for example `vision/` and `capture/` exist only if the screen source is chosen (Q1), and the C++ and Java files only if Q2 includes them.

## 2. Tree

```text
ai-coding-mentor/
├── .github/
│   └── workflows/
│       └── ci.yml  # PH0
├── backend/
│   ├── app/
│   │   ├── analysis/
│   │   │   ├── linters/
│   │   │   │   ├── base.py  # PH2
│   │   │   │   ├── cpp.py  # PH8 (Q2)
│   │   │   │   ├── java.py  # PH8 (Q2)
│   │   │   │   └── ruff_python.py  # PH2 (Q2)
│   │   │   ├── quality/
│   │   │   │   ├── complexity.py  # PH6
│   │   │   │   └── patterns.py  # PH6
│   │   │   ├── treesitter/
│   │   │   │   ├── queries/  # PH6
│   │   │   │   ├── errors.py  # PH2
│   │   │   │   └── parser.py  # PH2
│   │   │   ├── aggregator.py  # PH2
│   │   │   ├── pipeline.py  # PH1
│   │   │   ├── python_ast.py  # PH2 (Q2)
│   │   │   └── taxonomy.py  # PH2
│   │   ├── api/
│   │   │   ├── health.py  # PH1
│   │   │   ├── problems.py  # PH3 (Q3)
│   │   │   ├── progress.py  # PH6
│   │   │   └── sessions.py  # PH5
│   │   ├── core/
│   │   │   ├── errors.py  # PH1
│   │   │   ├── events.py  # PH1
│   │   │   ├── limits.py  # PH4
│   │   │   ├── logging.py  # PH1
│   │   │   └── security.py  # PH5 (Q5)
│   │   ├── db/
│   │   │   ├── base.py  # PH5
│   │   │   ├── models.py  # PH5
│   │   │   ├── repositories.py  # PH5
│   │   │   └── session.py  # PH5 (Q12)
│   │   ├── execution/
│   │   │   ├── client.py  # PH3
│   │   │   ├── result_parser.py  # PH3
│   │   │   └── test_runner.py  # PH3 (Q3)
│   │   ├── ingest/
│   │   │   ├── coalescer.py  # PH1
│   │   │   ├── redaction.py  # PH4
│   │   │   └── snapshot.py  # PH1
│   │   ├── learner/
│   │   │   ├── adaptation.py  # PH6
│   │   │   ├── metrics.py  # PH6 (Q9)
│   │   │   └── tracking.py  # PH5
│   │   ├── mentor/
│   │   │   ├── llm/
│   │   │   │   ├── base.py  # PH4
│   │   │   │   ├── openai_compatible.py  # PH4 (Q4)
│   │   │   │   └── registry.py  # PH4 (Q4)
│   │   │   ├── prompts/
│   │   │   │   ├── hint_levels.md  # PH4 (Q13)
│   │   │   │   └── system.md  # PH4
│   │   │   ├── cache.py  # PH4
│   │   │   ├── engine.py  # PH4
│   │   │   ├── fallback_explanations.py  # PH4 (Q8)
│   │   │   ├── guardrails.py  # PH4
│   │   │   ├── hint_ladder.py  # PH4 (Q13)
│   │   │   ├── prompt_builder.py  # PH4
│   │   │   └── trigger_policy.py  # PH4
│   │   ├── problems/
│   │   │   ├── seed/  # PH3 (Q3)
│   │   │   └── store.py  # PH3 (Q3)
│   │   ├── schemas/
│   │   │   ├── diagnostic.py  # PH1
│   │   │   ├── export.py  # PH1
│   │   │   ├── hint.py  # PH4
│   │   │   ├── problem.py  # PH3 (Q3)
│   │   │   ├── run.py  # PH3
│   │   │   ├── snapshot.py  # PH1
│   │   │   └── ws.py  # PH1
│   │   ├── vision/
│   │   │   ├── ocr/
│   │   │   │   └── base.py  # PH7 (Q1)
│   │   │   ├── code_region_detect.py  # PH7 (Q1)
│   │   │   └── region_tracking.py  # PH7 (Q1)
│   │   │   ├── code_reconstruct.py  # PH7 (Q1)
│   │   │   ├── frame_decode.py  # PH7 (Q1)
│   │   │   ├── language_detect.py  # PH7 (Q1)
│   │   │   └── preprocess.py  # PH7 (Q1)
│   │   ├── ws/
│   │   │   ├── connection_manager.py  # PH1
│   │   │   ├── endpoint.py  # PH1
│   │   │   └── handlers.py  # PH1
│   │   ├── __init__.py  # PH1
│   │   ├── config.py  # PH1
│   │   └── main.py  # PH1
│   ├── migrations/
│   │   ├── versions/  # PH5
│   │   └── env.py  # PH5
│   ├── tests/
│   │   ├── adversarial/  # PH4
│   │   ├── fixtures/
│   │   │   └── broken_snippets/  # PH2
│   │   ├── integration/  # PH1
│   │   ├── unit/  # PH1
│   │   └── conftest.py  # PH1
│   ├── alembic.ini  # PH5
│   ├── Dockerfile  # PH9
│   └── pyproject.toml  # PH0
├── docs/
│   ├── adr/  # PH0
│   ├── 00-PROJECT-BRIEF.md  # PH0
│   ├── 01-STACK-AND-ABSTRACT-REVIEW.md  # PH0
│   ├── 02-REQUIREMENTS.md  # PH0
│   ├── 03-ARCHITECTURE.md  # PH0
│   ├── 04-FOLDER-STRUCTURE.md  # PH0
│   ├── 05-IMPLEMENTATION-PLAN.md  # PH0
│   ├── 06-DEPENDENCIES-AND-COMMANDS.md  # PH0
│   ├── 07-TESTING-AND-VALIDATION.md  # PH0
│   ├── 08-ROLLBACK-AND-FAILURE-HANDLING.md  # PH0
│   ├── 09-RISKS-AND-EDGE-CASES.md  # PH0
│   ├── 10-OPEN-QUESTIONS.md  # PH0
│   ├── 11-FINAL-CHECKLIST.md  # PH0
│   └── 12-REVIEW-LOG.md  # PH0
├── eval/
│   ├── datasets/
│   │   ├── code_bugs/  # PH2
│   │   ├── code_regions/  # PH7 (Q1)
│   │   └── ocr_screens/  # PH7 (Q1)
│   ├── harness/
│   │   ├── bench_latency.py  # PH2
│   │   ├── judges.py  # PH4
│   │   ├── metrics.py  # PH2
│   │   ├── report.py  # PH2
│   │   └── run_eval.py  # PH2
│   ├── reports/  # PH2
│   └── README.md  # PH2
├── frontend/
│   ├── e2e/  # PH1
│   ├── src/
│   │   ├── components/
│   │   │   └── ui/  # PH0
│   │   ├── features/
│   │   │   ├── capture/
│   │   │   │   ├── CapturePanel.tsx  # PH7 (Q1)
│   │   │   │   ├── ConsentDialog.tsx  # PH7 (Q1)
│   │   │   │   ├── frameDiff.ts  # PH7 (Q1)
│   │   │   │   └── useScreenCapture.ts  # PH7 (Q1)
│   │   │   ├── editor/
│   │   │   │   ├── EditorPane.tsx  # PH1 (Q1)
│   │   │   │   └── markers.ts  # PH1
│   │   │   ├── mentor/
│   │   │   │   ├── HintCard.tsx  # PH4
│   │   │   │   └── MentorPanel.tsx  # PH4
│   │   │   ├── problems/
│   │   │   │   └── ProblemPanel.tsx  # PH3 (Q3)
│   │   │   ├── progress/
│   │   │   │   └── ProgressDashboard.tsx  # PH6
│   │   │   └── run/
│   │   │       ├── RunPanel.tsx  # PH3
│   │   │       └── TestResults.tsx  # PH3 (Q3)
│   │   ├── lib/
│   │   │   ├── api/
│   │   │   │   └── client.ts  # PH5
│   │   │   ├── ws/
│   │   │   │   ├── client.ts  # PH1
│   │   │   │   └── reconnect.ts  # PH1
│   │   │   └── utils.ts  # PH0
│   │   ├── routes/
│   │   │   ├── history.tsx  # PH5
│   │   │   ├── progress.tsx  # PH6
│   │   │   ├── settings.tsx  # PH4
│   │   │   └── workspace.tsx  # PH1
│   │   ├── store/
│   │   │   ├── session.ts  # PH1
│   │   │   └── settings.ts  # PH4
│   │   ├── test/
│   │   │   └── setup.ts  # PH0
│   │   ├── types/
│   │   │   └── generated/  # PH1
│   │   ├── App.tsx  # PH1
│   │   └── main.tsx  # PH0
│   ├── components.json  # PH0
│   ├── Dockerfile  # PH9
│   ├── index.html  # PH0
│   ├── package.json  # PH0
│   ├── tsconfig.json  # PH0
│   └── vite.config.ts  # PH0
├── sandbox/
│   ├── images/
│   │   ├── cpp/
│   │   │   └── Dockerfile  # PH8 (Q2)
│   │   ├── java/
│   │   │   └── Dockerfile  # PH8 (Q2)
│   │   └── python/
│   │       └── Dockerfile  # PH3 (Q2)
│   ├── runner/
│   │   ├── app.py  # PH3
│   │   ├── languages.py  # PH3 (Q2)
│   │   └── policy.py  # PH3
│   ├── tests/  # PH3
│   ├── pyproject.toml  # PH3
│   └── README.md  # PH3
├── .env.example  # PH0
├── .gitignore  # PH0
├── CLAUDE.md  # PH0
├── docker-compose.yml  # PH0
├── Makefile  # PH0
└── README.md  # PH0
```

Folder entries end with `/`. The tag after `#` is the phase that creates the entry and, in brackets, the question that gates it.

## 3. Dependency rules

Backend layers; a module may import only from layers below it.

1. `schemas`, `core` — foundation. `schemas` imports nothing from the app.
2. `ingest`, `problems`, `db` — data in and out.
3. `analysis`, `execution`, `vision` — produce diagnostics.
4. `mentor` — may use `schemas`, `core`, `ingest/redaction.py` and `analysis/taxonomy.py`; never `db` or `ws`.
5. `learner` — may use `schemas`, `core`, `db/repositories.py` and `ingest/redaction.py`; reacts to events.
6. `ws`, `api` — transport only, no business logic.
7. `main.py` — the composition root: the only place that wires modules and reads feature flags.

Rules that tests and review enforce (an architecture test checks the import layering and forbids executing learner text):

- Nothing imports `ws` or `api` except `main.py`.
- Only `backend/app/db/repositories.py` runs queries.
- Learner code never runs outside `sandbox/`. `backend/app/analysis/python_ast.py` compiles text and never executes it.
- `backend/app/vision/` is imported only from `main.py` and `backend/app/ws/handlers.py`, behind `FEATURE_SCREEN_SOURCE`.
- Analyzers return values; orchestrators publish events. An analyzer never imports the event bus.
- Prompts live only in `backend/app/mentor/prompts/`.
- `backend/app/schemas/` models are the single source for contracts; `frontend/src/types/generated/` is never edited by hand.

Frontend rules:

- Folders under `frontend/src/features/` do not import each other; shared pieces go to `frontend/src/components/` or `frontend/src/lib/`.
- `frontend/src/lib/` never imports from `frontend/src/features/`.
- Network access only through `frontend/src/lib/ws/` and `frontend/src/lib/api/`.
- Model text is rendered as text; never use `dangerouslySetInnerHTML` for it.

## 4. Naming

| Thing | Convention |
|---|---|
| Python modules and functions | `snake_case`; classes `PascalCase` |
| Pydantic models | singular nouns (`Diagnostic`, `Hint`) |
| Backend tests | `test_<module>.py`, mirroring the `backend/app/` tree |
| React components | `PascalCase.tsx`; hooks `useThing.ts`; other files `camelCase.ts` |
| Environment variables | `UPPER_SNAKE_CASE`, all documented in `.env.example` |
| ADRs | `docs/adr/NNNN-short-title.md` |
| Eval cases | `eval/datasets/code_bugs/<language>/<case_id>.<ext>` plus `<case_id>.json` holding category, expected lines, clean flag and notes |
| Branches and tags | `phase/<n>-<slug>`, `phase-<n>-complete` |

## 5. Where new things go

| If you are adding | Put it in |
|---|---|
| A new diagnostic source (linter, checker) | `backend/app/analysis/linters/` plus a taxonomy mapping |
| A new learner language | Follow PH8; never edit unrelated modules |
| A new WebSocket message | `backend/app/schemas/ws.py`, regenerate types, add a handler, write an ADR (contract change) |
| A new prompt or level instruction | `backend/app/mentor/prompts/` and bump its version |
| A new metric | `backend/app/learner/metrics.py` and the dashboard |
| A new environment variable | `backend/app/config.py` and `.env.example` |
| A new sandbox limit | `sandbox/runner/policy.py` plus an isolation test |
| A decision that changes the plan | `docs/adr/` and the affected planning file |

## 6. Generated and ignored

| Path | Status |
|---|---|
| `frontend/src/types/generated/` | Generated, committed, checked in CI |
| `eval/reports/` | Generated, gitignored |
| `.env` | Local only, gitignored |
| Build output, caches, virtual environments | Gitignored |

## 7. File manifest

Phase = when the entry is created. Priority and Gate come from `02-REQUIREMENTS.md` and `10-OPEN-QUESTIONS.md`. In this bundle the tree, the manifest and the per-phase file lists in `05-IMPLEMENTATION-PLAN.md` are plain text: when an answer adds or removes files, update all three together (PH0-S1 does this).

| Phase | New files and folders |
|---|---|
| PH0 | 31 |
| PH1 | 29 |
| PH2 | 15 |
| PH3 | 18 |
| PH4 | 22 |
| PH5 | 12 |
| PH6 | 8 |
| PH7 | 14 |
| PH8 | 4 |
| PH9 | 2 |
| **Total** | **155** |

| Path | Phase | Priority | Gate | Purpose |
|---|---|---|---|---|
| `.env.example` | PH0 | P0 | - | Every environment variable documented; contains no secrets |
| `.github/workflows/ci.yml` | PH0 | P0 | - | CI gates (D8): lint, type-check, tests, generated-types check, sandbox tests |
| `.gitignore` | PH0 | P0 | - | Ignore env files, caches, build output, eval reports |
| `CLAUDE.md` | PH0 | P0 | - | Agent operating manual: status, execution rules, safety rules (delivered with this plan) |
| `Makefile` | PH0 | P0 | - | Task runner (D9); the underlying commands are listed in docs/06 |
| `README.md` | PH0 | P0 | - | Human quickstart; stub at PH0, finalised at PH9 |
| `backend/Dockerfile` | PH9 | P1 | - | API container image for deployment |
| `backend/alembic.ini` | PH5 | P0 | - | Alembic configuration |
| `backend/app/__init__.py` | PH1 | P0 | - | Package marker |
| `backend/app/analysis/aggregator.py` | PH2 | P0 | - | Dedupe, rank and fingerprint diagnostics |
| `backend/app/analysis/linters/base.py` | PH2 | P0 | - | Linter wrapper interface |
| `backend/app/analysis/linters/cpp.py` | PH8 | P1 | Q2 | C++ linter wrapper (only if Q2 includes C++) |
| `backend/app/analysis/linters/java.py` | PH8 | P1 | Q2 | Java linter wrapper (only if Q2 includes Java) |
| `backend/app/analysis/linters/ruff_python.py` | PH2 | P0 | Q2 | Ruff wrapper (subprocess, JSON output) |
| `backend/app/analysis/pipeline.py` | PH1 | P0 | - | Fast-path orchestrator (stub in PH1, real analyzers from PH2) |
| `backend/app/analysis/python_ast.py` | PH2 | P0 | Q2 | Precise Python syntax errors via the standard library in a limited worker |
| `backend/app/analysis/quality/complexity.py` | PH6 | P1 | - | Complexity and nesting metrics |
| `backend/app/analysis/quality/patterns.py` | PH6 | P1 | - | Performance and quality pattern detectors |
| `backend/app/analysis/taxonomy.py` | PH2 | P0 | - | Mistake taxonomy and tool-rule mapping |
| `backend/app/analysis/treesitter/errors.py` | PH2 | P0 | - | Extract ERROR and MISSING nodes as syntax diagnostics |
| `backend/app/analysis/treesitter/parser.py` | PH2 | P0 | - | Tree-sitter parser registry per language |
| `backend/app/analysis/treesitter/queries/` | PH6 | P1 | - | Tree-sitter queries for quality and performance patterns |
| `backend/app/api/health.py` | PH1 | P0 | - | Liveness and readiness endpoint |
| `backend/app/api/problems.py` | PH3 | P0 | Q3 | Problem and test-case endpoints (only if Q3 includes a bank) |
| `backend/app/api/progress.py` | PH6 | P1 | - | Progress and analytics endpoints |
| `backend/app/api/sessions.py` | PH5 | P0 | - | Session history endpoints |
| `backend/app/config.py` | PH1 | P0 | - | Typed settings from environment (pydantic-settings) |
| `backend/app/core/errors.py` | PH1 | P0 | - | Error types and WS/REST error mapping |
| `backend/app/core/events.py` | PH1 | P0 | - | In-process typed async event bus |
| `backend/app/core/limits.py` | PH4 | P0 | - | Rate limits and LLM/run budgets |
| `backend/app/core/logging.py` | PH1 | P0 | - | Structured JSON logging with correlation IDs |
| `backend/app/core/security.py` | PH5 | P0 | Q5 | Identity and auth: single local profile or authenticated users |
| `backend/app/db/base.py` | PH5 | P0 | - | Declarative base and naming conventions |
| `backend/app/db/models.py` | PH5 | P0 | - | ORM models per `03-ARCHITECTURE.md` section 7 |
| `backend/app/db/repositories.py` | PH5 | P0 | - | The only module that runs queries |
| `backend/app/db/session.py` | PH5 | P0 | Q12 | Async engine and session factory |
| `backend/app/execution/client.py` | PH3 | P0 | - | HTTP client for the sandbox runner (timeouts, circuit breaker) |
| `backend/app/execution/result_parser.py` | PH3 | P0 | - | Runner output to runtime Diagnostics (traceback line mapping) |
| `backend/app/execution/test_runner.py` | PH3 | P0 | Q3 | Run test cases and compare output (only if Q3 includes tests) |
| `backend/app/ingest/coalescer.py` | PH1 | P0 | - | Latest-wins coalescing per session using seq |
| `backend/app/ingest/redaction.py` | PH4 | P0 | - | Secret redaction before any LLM call |
| `backend/app/ingest/snapshot.py` | PH1 | P0 | - | Normalise and validate incoming snapshots |
| `backend/app/learner/adaptation.py` | PH6 | P1 | - | Rule-based hint adaptation from the mistake record |
| `backend/app/learner/metrics.py` | PH6 | P1 | Q9 | Progress metric queries |
| `backend/app/learner/tracking.py` | PH5 | P0 | - | Issue lifecycle and checkpoint persistence driven by events |
| `backend/app/main.py` | PH1 | P0 | - | App factory and composition root: routers, WS route, event subscriptions |
| `backend/app/mentor/cache.py` | PH4 | P0 | - | Hint cache keyed by code, diagnostics, level, prompt version and model |
| `backend/app/mentor/engine.py` | PH4 | P0 | - | Orchestrates trigger, prompt, LLM, guardrails, hint |
| `backend/app/mentor/fallback_explanations.py` | PH4 | P0 | Q8 | Template explanations per category for H1 to H3 (no LLM needed) |
| `backend/app/mentor/guardrails.py` | PH4 | P0 | - | Schema, level-compliance, grounding and leakage checks; retry and fallback |
| `backend/app/mentor/hint_ladder.py` | PH4 | P0 | Q13 | Per-issue hint-level state machine (H1 to H4) |
| `backend/app/mentor/llm/base.py` | PH4 | P0 | - | LLMProvider interface and result types |
| `backend/app/mentor/llm/openai_compatible.py` | PH4 | P0 | Q4 | Adapter for LM Studio, Ollama, vLLM and hosted OpenAI-compatible APIs |
| `backend/app/mentor/llm/registry.py` | PH4 | P0 | Q4 | Provider selection from settings |
| `backend/app/mentor/prompt_builder.py` | PH4 | P0 | - | Build delimited prompts from verified inputs |
| `backend/app/mentor/prompts/hint_levels.md` | PH4 | P0 | Q13 | Versioned per-level instructions |
| `backend/app/mentor/prompts/system.md` | PH4 | P0 | - | Versioned system prompt |
| `backend/app/mentor/trigger_policy.py` | PH4 | P0 | - | When to speak: settle, persist, cooldown, explicit, proactivity |
| `backend/app/problems/seed/` | PH3 | P0 | Q3 | Seed problems and test cases as data files (hidden flags, limits) |
| `backend/app/problems/store.py` | PH3 | P0 | Q3 | ProblemStore interface: file-backed in PH3, database-backed from PH5 |
| `backend/app/schemas/diagnostic.py` | PH1 | P0 | - | Diagnostic, Range and Category models |
| `backend/app/schemas/export.py` | PH1 | P0 | - | Export JSON Schema from the models for the TypeScript type generator |
| `backend/app/schemas/hint.py` | PH4 | P0 | - | Hint, level and mentor-output models |
| `backend/app/schemas/problem.py` | PH3 | P0 | Q3 | Problem and TestCase models |
| `backend/app/schemas/run.py` | PH3 | P0 | - | RunRequest and RunResult models |
| `backend/app/schemas/snapshot.py` | PH1 | P0 | - | CodeSnapshot model |
| `backend/app/schemas/ws.py` | PH1 | P0 | - | WebSocket envelope and payload models (source of the generated TypeScript types) |
| `backend/app/vision/code_region_detect.py` | PH7 | P1 | Q1 | Automatic code/editor region discovery using multi-signal scoring |
| `backend/app/vision/region_tracking.py` | PH7 | P1 | Q1 | Track the selected code region across frames and handle reacquisition |
| `backend/app/vision/code_reconstruct.py` | PH7 | P1 | Q1 | Lines and indentation from OCR boxes; strip gutters and line numbers |
| `backend/app/vision/frame_decode.py` | PH7 | P1 | Q1 | Decode and validate incoming frames |
| `backend/app/vision/language_detect.py` | PH7 | P1 | Q1 | Language guess by parse score when not declared |
| `backend/app/vision/ocr/base.py` | PH7 | P1 | Q1 | OCR engine interface (the engine file is added after the bake-off) |
| `backend/app/vision/preprocess.py` | PH7 | P1 | Q1 | OpenCV preprocessing for OCR |
| `backend/app/ws/connection_manager.py` | PH1 | P0 | - | One active connection per session; send helpers |
| `backend/app/ws/endpoint.py` | PH1 | P0 | - | WebSocket route, Origin check, auth hook, message size limits |
| `backend/app/ws/handlers.py` | PH1 | P0 | - | Turn client messages into events; send server messages |
| `backend/migrations/env.py` | PH5 | P0 | - | Alembic environment (async engine) |
| `backend/migrations/versions/` | PH5 | P0 | - | Migration scripts, each with a working downgrade |
| `backend/pyproject.toml` | PH0 | P0 | - | Python project and dependency pins (uv); Ruff, pytest and type-checker config |
| `backend/tests/adversarial/` | PH4 | P0 | - | Guardrail and prompt-injection tests |
| `backend/tests/conftest.py` | PH1 | P0 | - | Shared fixtures (app, WS client, fake LLM, fake runner) |
| `backend/tests/fixtures/broken_snippets/` | PH2 | P0 | - | Learner-typical broken code shared by tests and evals |
| `backend/tests/integration/` | PH1 | P0 | - | Integration tests (WebSocket flow, database, failure drills) |
| `backend/tests/unit/` | PH1 | P0 | - | Unit tests |
| `docker-compose.yml` | PH0 | P0 | - | PostgreSQL first; sandbox runner and optional services added in later phases |
| `docs/00-PROJECT-BRIEF.md` | PH0 | P0 | - | Your template, filled in |
| `docs/01-STACK-AND-ABSTRACT-REVIEW.md` | PH0 | P0 | - | Verdict on every abstract claim and stack item |
| `docs/02-REQUIREMENTS.md` | PH0 | P0 | - | Requirement IDs, priorities, gates, phases |
| `docs/03-ARCHITECTURE.md` | PH0 | P0 | - | Components, flows, contracts, data model, safety design |
| `docs/04-FOLDER-STRUCTURE.md` | PH0 | P0 | - | Repo tree, import rules, file manifest |
| `docs/05-IMPLEMENTATION-PLAN.md` | PH0 | P0 | - | Phases, steps, verification, exit criteria |
| `docs/06-DEPENDENCIES-AND-COMMANDS.md` | PH0 | P0 | - | Dependencies, environment variables, commands |
| `docs/07-TESTING-AND-VALIDATION.md` | PH0 | P0 | - | Traceability matrix, suites, acceptance scenarios |
| `docs/08-ROLLBACK-AND-FAILURE-HANDLING.md` | PH0 | P0 | - | Phase rollback, kill switches, failure matrix |
| `docs/09-RISKS-AND-EDGE-CASES.md` | PH0 | P0 | - | Risk register and edge cases |
| `docs/10-OPEN-QUESTIONS.md` | PH0 | P0 | - | Questions, provisional defaults, decision log |
| `docs/11-FINAL-CHECKLIST.md` | PH0 | P0 | - | Readiness, phase-exit and release checklists |
| `docs/12-REVIEW-LOG.md` | PH0 | P0 | - | Record of the three review cycles |
| `docs/adr/` | PH0 | P0 | - | Architecture decision records: one per answered question or major choice |
| `eval/README.md` | PH2 | P0 | - | How to run and read evaluations |
| `eval/datasets/code_bugs/` | PH2 | P0 | - | Labelled buggy and clean snippets per language |
| `eval/datasets/code_regions/` | PH7 | P1 | Q1 | Screenshots annotated with ground-truth code-region geometry and distractors |
| `eval/datasets/ocr_screens/` | PH7 | P1 | Q1 | Screenshots with ground-truth text |
| `eval/harness/bench_latency.py` | PH2 | P0 | - | Replay typing traces and measure latency percentiles |
| `eval/harness/judges.py` | PH4 | P0 | - | Automatic hint checks and optional LLM-judge scoring |
| `eval/harness/metrics.py` | PH2 | P0 | - | Precision, recall, CER and related metrics |
| `eval/harness/report.py` | PH2 | P0 | - | Write reports to eval/reports/ |
| `eval/harness/run_eval.py` | PH2 | P0 | - | Evaluation entry point (suites: analysis, hints, ocr) |
| `eval/reports/` | PH2 | P0 | - | Generated reports (gitignored) |
| `frontend/Dockerfile` | PH9 | P1 | - | Production build image |
| `frontend/components.json` | PH0 | P0 | - | shadcn/ui configuration |
| `frontend/e2e/` | PH1 | P0 | - | Playwright end-to-end specs for acceptance scenarios |
| `frontend/index.html` | PH0 | P0 | - | App entry HTML |
| `frontend/package.json` | PH0 | P0 | - | Dependencies and scripts (pnpm) |
| `frontend/src/App.tsx` | PH1 | P0 | - | App shell and router |
| `frontend/src/components/ui/` | PH0 | P0 | - | shadcn/ui generated components |
| `frontend/src/features/capture/CapturePanel.tsx` | PH7 | P1 | Q1 | Share, region select, pause, stop, indicator, and a read-back view of the reconstructed code |
| `frontend/src/features/capture/ConsentDialog.tsx` | PH7 | P1 | Q1 | Explicit consent before any capture |
| `frontend/src/features/capture/frameDiff.ts` | PH7 | P1 | Q1 | Client-side change and settle detection |
| `frontend/src/features/capture/useScreenCapture.ts` | PH7 | P1 | Q1 | getDisplayMedia lifecycle and sampling |
| `frontend/src/features/editor/EditorPane.tsx` | PH1 | P0 | Q1 | Monaco editor bundled locally; emits debounced snapshots |
| `frontend/src/features/editor/markers.ts` | PH1 | P0 | - | Diagnostics to Monaco markers |
| `frontend/src/features/mentor/HintCard.tsx` | PH4 | P0 | - | Hint display with sanitised rendering and feedback buttons |
| `frontend/src/features/mentor/overlayPosition.ts` | PH7 | P1 | Q1 | Position the overlay near detected code while avoiding obstruction |
| `frontend/src/features/mentor/MentorPanel.tsx` | PH4 | P0 | - | Issues list, hint ladder controls, notices |
| `frontend/src/features/mentor/FloatingMentor.tsx` | PH4 | P0 | - | Movable floating mentor overlay for live feedback |
| `frontend/src/features/problems/ProblemPanel.tsx` | PH3 | P0 | Q3 | Problem picker and statement view |
| `frontend/src/features/progress/ProgressDashboard.tsx` | PH6 | P1 | - | Charts built with shadcn/ui chart components |
| `frontend/src/features/run/RunPanel.tsx` | PH3 | P0 | - | Run button, stdin, output and status |
| `frontend/src/features/run/TestResults.tsx` | PH3 | P0 | Q3 | Test case results (hidden tests show pass or fail only) |
| `frontend/src/lib/api/client.ts` | PH5 | P0 | - | Typed REST client |
| `frontend/src/lib/utils.ts` | PH0 | P0 | - | shadcn/ui class-name helper |
| `frontend/src/lib/ws/client.ts` | PH1 | P0 | - | Typed WebSocket client with seq numbers |
| `frontend/src/lib/ws/reconnect.ts` | PH1 | P0 | - | Backoff, jitter and resync logic |
| `frontend/src/main.tsx` | PH0 | P0 | - | App bootstrap |
| `frontend/src/routes/history.tsx` | PH5 | P0 | - | Session and issue history: the learner's record of mistakes |
| `frontend/src/routes/progress.tsx` | PH6 | P1 | - | Progress dashboard route |
| `frontend/src/routes/settings.tsx` | PH4 | P0 | - | Mentor proactivity and display settings |
| `frontend/src/routes/workspace.tsx` | PH1 | P0 | - | Editor, diagnostics, run and mentor panels |
| `frontend/src/store/session.ts` | PH1 | P0 | - | Session, snapshot, diagnostics and issues state |
| `frontend/src/store/settings.ts` | PH4 | P0 | - | User settings state |
| `frontend/src/test/setup.ts` | PH0 | P0 | - | Vitest setup |
| `frontend/src/types/generated/` | PH1 | P0 | - | TypeScript types generated from backend schemas (never edited by hand) |
| `frontend/tsconfig.json` | PH0 | P0 | - | TypeScript strict configuration |
| `frontend/vite.config.ts` | PH0 | P0 | - | Vite config with Tailwind plugin and path alias |
| `sandbox/README.md` | PH3 | P0 | - | Threat model, policy and how to run the runner |
| `sandbox/images/cpp/Dockerfile` | PH8 | P1 | Q2 | C++ sandbox image (only if Q2 includes C++) |
| `sandbox/images/java/Dockerfile` | PH8 | P1 | Q2 | Java sandbox image (only if Q2 includes Java) |
| `sandbox/images/python/Dockerfile` | PH3 | P0 | Q2 | Python sandbox image (non-root, minimal) |
| `sandbox/pyproject.toml` | PH3 | P0 | - | Runner dependencies, separate from the API |
| `sandbox/runner/app.py` | PH3 | P0 | - | Runner service: accepts jobs, enforces policy, returns results |
| `sandbox/runner/languages.py` | PH3 | P0 | Q2 | Per-language compile and run command templates |
| `sandbox/runner/policy.py` | PH3 | P0 | - | Limits and container flags (time, memory, PIDs, output, no network) |
| `sandbox/tests/` | PH3 | P0 | - | Isolation and limit tests (must pass before merge) |
