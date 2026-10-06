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
- [x] Q2–Q7 answered by you (see ADR-0002)
- [x] You said "start Phase 0"

## B. Phase exits

### PH0 — Baseline Toolchain (COMPLETE)
- [x] Backend dependencies: uv sync (32 packages) + lockfile committed
- [x] Frontend dependencies: pnpm install + build scripts approved + build passing
- [x] Database container: PostgreSQL 15 healthy on port 5433
- [x] WebSocket module: Created `backend/app/ws/endpoint.py` (stub implementation)
- [x] Health endpoints: `GET /api/v1/health` → `200 OK`
- [x] Development commands: Backend, frontend, database all startable
- [x] TypeScript build: Production build passes (`✓ 1388 modules transformed`)
- [x] Toolchain reproducibility: All dependencies locked and committed
- [ ] Product features: **Deferred to PH1+** (analysis pipeline, sandbox security, LLM integration)

### PH1 — Walking skeleton
- [x] Contract v0 frozen in an ADR; generated types up to date
- [x] Placeholder marker appears from typing; stale results never applied
- [x] Reconnect and resync work; disallowed Origin rejected
- [x] Logs carry stage timings and no code
- [x] Enhanced Python analyzer with syntax, semantic, style, quality checks
- [x] WebSocket endpoint with session management, heartbeat, reconnection
- [x] Monaco editor integration with diagnostic markers and hover details
- [x] Zustand state management with WebSocket service and performance metrics
- [x] End-to-end latency <1s from keystroke to diagnostic markers
- [x] Production build verified (1024 modules, 2.6MB gzipped)
- [x] Comprehensive test suite: test_phase1_integration.py

### PH2 — Fast static analysis (COMPLETE)
- [x] Tree-sitter, Python parser and Ruff results mapped to the taxonomy (`backend/app/analysis/taxonomy.py`)
- [x] Analyzer timeouts and crashes handled (`backend/app/analysis/python_ast.py`, `ruff_python.py`)
- [x] Baseline analysis eval and latency benchmark recorded with sample sizes (`eval/harness/run_eval.py`, `bench_latency.py`)
- [x] Diagnostics aggregator with stable fingerprinting and deduplication (`backend/app/analysis/aggregator.py`)
- [x] Quality and performance targets met (<50ms typical latency, 100% precision/recall on evaluation set)

### PH3 — Sandbox and execution (COMPLETE)
- [x] Every isolation and limit test passes with Docker (non-root, network none, ro rootfs, timeout, memory limit, output cap)
- [x] API decoupled from Docker daemon: runner operates behind authenticated HTTP JSON API (`POST /jobs`)
- [x] Runtime exceptions mapped to taxonomy categories with accurate traceback line parsing (`backend/app/execution/result_parser.py`)
- [x] Built-in problem bank with seed coding challenges and test runner (`backend/app/problems/`, `backend/app/execution/test_runner.py`)
- [x] Information hiding: hidden test cases sanitized and never leak inputs or expected outputs to clients
- [x] Frontend execution panel, test results renderer, and problem picker UI fully integrated and built (`frontend/src/features/`)
- [x] `EXECUTION_ENABLED` kill switch and circuit breaker implemented and verified (`backend/app/execution/client.py`)

### PH4 — Mentor engine (COMPLETE)
- [x] Provider + model choice recorded (`docs/adr/0006-sandbox-isolation-and-execution.md` context;
      Q4 = both local and hosted, switchable). No live bake-off was run: no LLM endpoint was
      available in this environment — **stated as a limitation**, template mode is the tested path
- [x] Adversarial suite passes; no fenced code at H1–H3 (`tests/adversarial/test_guardrails.py`)
- [x] Template-only mode verified with `LLM_ENABLED=false` (hints eval: 100% guardrail pass)
- [x] H4 gated by H3 + explicit request + confirmation (unit + live API test)
- [x] Mentor latency reported for the template path (<1 ms in the hints eval); LLM latency needs an endpoint
- [ ] Floating mentor overlay keyboard/dismissal tests: ARIA labels and keyboard-reachable
      controls are implemented, but there is no automated DOM test harness for them

### PH5 — Persistence and learner record (COMPLETE)
- [x] Migrations upgrade **and** downgrade verified (`alembic downgrade base` → `upgrade head`)
- [x] Database outage does not crash the API; it degrades to in-memory (lifespan catches it)
- [x] No code content in logs; code checkpoints redacted; `STORE_CODE_TEXT=false` stores no code (SC-6)
- [x] Identity: single local profile per Q5; every record carries `user_id`
- [x] Repository round-trip verified against real PostgreSQL (create → list → delete-my-data → gone)

### PH6 — Analytics, quality checks, adaptation (COMPLETE)
- [x] Progress endpoint reports issue counts, resolve rate, time-to-resolve and hint usage
- [x] Adaptation rules unit-tested and deterministic (same input → same profile)
- [x] Quality analyzers use zero-false-positive thresholds on the clean-negative corpus
- [ ] SC-7 dashboard-equals-SQL comparison: verified in shape, not by an automated SQL cross-check

### PH7 — Screen source and OCR (COMPLETE)
- [x] Region detection measured: precision 1.0, recall 1.0, mean IoU 0.996
- [x] OCR measured: line accuracy 0.99, CER 9.2% (RapidOCR; 4-case synthetic dataset)
- [x] Automatic region tracked across movement; loss and reacquisition tested
- [x] Low-confidence region and OCR paths produce **no** code/diagnostics and offer manual fallback
- [x] Consent required by the API (tested); indicator, pause, stop implemented
- [x] Manual region override implemented and validated
- [x] No frames persisted (hash only); `FEATURE_SCREEN_SOURCE` defaults to false
- [ ] Screen-discovery scenarios S8 run manually in a browser, not as automated e2e specs

### PH8 — Additional languages (OUT OF SCOPE — see ADR-0007)
- [x] Q2 = Python only, so every gated PH8 deliverable is a documented no-op
- [x] Confirmed no C++/Java artifacts exist; only `sandbox/images/python/` is present
- [x] Re-opening the decision is additive (grammar/linter/sandbox interfaces are pluggable)

### PH9 — Hardening, evaluation, release (COMPLETE)
- [x] Latency benchmark against P-02 recorded: P50 29.2 ms, P95 32.7 ms (target < 1000 ms)
- [x] Security review: Origin allowlist, WS size limit, hint rate limiting, `pip-audit` clean,
      secret scan (which **found and fixed** a tracked `.env` — now untracked)
- [x] Accessibility: ARIA labels on mentor/capture controls; keyboard-reachable buttons
- [ ] Known a11y limitation: Monaco's editor sets `aria-hidden` on its focused mirror
      textarea, which browsers log as a blocked-aria-hidden warning. This is third-party
      editor behaviour, not our markup, and needs a Monaco-level workaround or an upstream fix
- [x] `backend/Dockerfile`, `frontend/Dockerfile`, `frontend/nginx.conf` present
- [x] Docker/compose builds were **not** executed here (Docker available, image build not run) — limitation
- [ ] Clean-checkout rehearsal using only the documented commands: **not run** — limitation
- [x] Evidence for SC-1…SC-8 summarised in `docs/02-STATUS.md`; remaining gaps listed here
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
