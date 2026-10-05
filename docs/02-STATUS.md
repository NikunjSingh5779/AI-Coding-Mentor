# 02 — Project Status

**Current Status:** Phase 3 Complete ✅ — Ready for Phase 4  
**Last Updated:** 2026-10-05  
**Branch:** `phase/3-sandbox-execution`

## ✅ Phase 0 Achievements

**Toolchain Established**
- Backend: FastAPI + uv dependencies (32 packages) installed and locked
- Frontend: React + Vite + TypeScript + pnpm build passing (`✓ 1024 modules transformed`)
- Database: PostgreSQL 15 container healthy on port 5433
- WebSocket: Full implementation with session management

## ✅ Phase 1 Achievements

**Real-Time Analysis Pipeline**
- Enhanced Python Analyzer with syntax and semantic diagnostics
- WebSocket Real-Time Pipeline with session management and coalescing
- Monaco Code Editor and Diagnostic Panels connected via Zustand state
- Performance: <1s end-to-end latency from keystroke to diagnostic display

## ✅ Phase 2 Achievements

**Fast Static Analysis Pipeline**
- **Taxonomy Mapping (`backend/app/analysis/taxonomy.py`)**
  - Mapped 23 fine-grained mistake categories across 8 groups
- **Diagnostics Aggregator (`backend/app/analysis/aggregator.py`)**
  - Content-aware stable hashing and deduplication per line/token
- **Tree-sitter Parser & Error Extraction (`backend/app/analysis/treesitter/`)**
  - Error-tolerant AST parsing with grammar registry
- **Standard Library AST Parser (`backend/app/analysis/python_ast.py`)**
  - Safe syntax checking without code execution
- **Ruff Linter Subprocess Wrapper (`backend/app/analysis/linters/ruff_python.py`)**
  - Stdin streaming and JSON output parsing
- **Evaluation Suite (`eval/`)**
  - Labeled dataset of clean and buggy snippets (`eval/datasets/code_bugs/`)
  - 100% precision & recall on benchmark suite; latency P95 ~31ms

## ✅ Phase 3 Achievements

**Sandbox and Execution Pipeline**
- **Threat Model & Isolation Policy (`sandbox/README.md`, `docs/adr/0006-sandbox-isolation-and-execution.md`)**
  - Hardened container execution policy (P-08/P-09): non-root (`sandbox:sandbox`, UID 1000), read-only rootfs, in-memory tmpfs `/work`, network disabled (`--network none`), all capabilities dropped (`ALL`), `no-new-privileges:true`, PID limit 64, memory cap 256MB, CPU quota 1.0 core, 64 KB output cap.
- **Python Sandbox Docker Image (`sandbox/images/python/Dockerfile`)**
  - Minimal non-root Python 3.11 image stripped of network utilities.
- **Sandbox Runner Service (`sandbox/runner/app.py`, `policy.py`, `languages.py`)**
  - Asynchronous FastAPI runner on port 8100 behind shared-secret authentication (`SANDBOX_SECRET`).
  - Strict concurrency limiter (`max_concurrent_jobs = 2`) returning `429 / runner_busy`.
  - Base64 tmpfs code injection and in-container process orchestration.
- **Isolation & Limit Verification (`sandbox/tests/`)**
  - 9/9 automated isolation and limit tests passing (non-root UID, blocked sockets, read-only rootfs, no Docker socket, infinite loop timeout, memory bomb containment, output truncation, stdin piping, test suite execution).
- **Backend Execution Engine (`backend/app/execution/`)**
  - `SandboxClient`: HTTP client with circuit breaker, timeout management, and `EXECUTION_ENABLED` kill switch.
  - `result_parser.py`: Maps runtime tracebacks and exit codes to taxonomy categories (e.g. `RUNTIME_ZERO_DIVISION`, `RUNTIME_INDEX`, `RUNTIME_TIMEOUT`, `RUNTIME_MEMORY`).
  - `test_runner.py`: Executes automated test suites while strictly redacting hidden test inputs and expected outputs (Q3 information hiding).
- **Problem Bank & Seed Challenges (`backend/app/problems/`, `backend/app/api/problems.py`)**
  - Seed challenges: Two Sum, Fibonacci, Valid Palindrome, FizzBuzz, Valid Parentheses, Reverse Words.
  - Public problem endpoints and submission execution.
- **Frontend Execution UI (`frontend/src/features/`)**
  - `ProblemPanel.tsx`: Interactive challenge browser with difficulty badges and sample cases.
  - `RunPanel.tsx`: Tabbed execution console for single runs, custom stdin, and automated test suite evaluation.
  - `TestResults.tsx`: Test case pass/fail summary and execution timings.

## 📊 Current Metrics

- **Backend tests:** 23/23 passing
- **Sandbox isolation tests:** 9/9 passing
- **Evaluation precision / recall:** 1.0 / 1.0 (100% on benchmark cases)
- **Analysis latency:** P50 ~29ms, P95 ~31ms (<50ms target met)
- **Frontend build:** Clean production build passing (`✓ 1029 modules transformed`)

## ⏭️ Next Phase: PH4 — Mentor Engine

**Scope:** Progressive 4-level hint ladder (H1 orientation to H4 solution reveal), LLM integration (local LM Studio / Ollama + hosted APIs), secret redaction, template fallback explanations, and strict anti-leakage guardrails.
