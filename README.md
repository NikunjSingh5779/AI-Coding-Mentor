# AI Coding Mentor

AI Coding Mentor is a real-time coding workspace that combines static analysis, isolated execution, verified problem tests, progressive AI mentoring, analytics, screen/OCR analysis, and floating mentor overlays.

## Architecture

```text
Monaco Editor
    |
    +-- WebSocket -> AST + Tree-sitter + Ruff -> diagnostics
    +-- Run -> dedicated sandbox runner -> isolated process
    +-- Problems -> verified public tests + server-side reference solution
    +-- Mentor -> diagnostics + OpenAI-compatible local/hosted LLM
    +-- Analytics -> persisted session history
    +-- Screen -> OCR -> code-region confidence gate -> same analyzer
```

## Floating mentor

The project has two floating modes:

- In-browser draggable mentor: collapsible, pinned/floating, H1-H4 controls and feedback.
- Desktop always-on-top mentor: PyQt6 companion modeled on the frameless/draggable/status/menu interaction pattern used by `ai-screener`.

## Phase status

| Phase | Capability | State |
|---|---|---|
| PH0 | Toolchain / CI / configuration | ✅ |
| PH1 | WebSocket real-time analysis + Monaco | ✅ |
| PH2 | AST + Tree-sitter + Ruff + aggregation | ✅ |
| PH3 | Dedicated Docker sandbox + execution/tests | ✅ |
| PH4 | Progressive mentor + LLM + fallback | ✅ |
| PH5 | Persistent sessions + retention | ✅ |
| PH6 | Analytics + adaptation | ✅ |
| PH7 | Screen capture + OCR + region tracking | ✅ |
| PH8 | Python / JavaScript / C++ / Java execution | ✅ |
| PH9 | CI, smoke tests, hardening and documentation | ✅ feature-complete; clean CI verification still required |

## Quick start

Prerequisites:

- Docker Desktop with Compose
- Node.js 24+ and pnpm 11+
- Python 3.11+ and uv
- Git
- Optional local OpenAI-compatible model server such as llama.cpp, LM Studio or Ollama

Create the environment file:

```bash
cp .env.example .env
```

Start the complete stack:

```bash
docker compose up --build
```

Open `http://localhost:5173`.

Services:

```text
Frontend       http://localhost:5173
Backend        http://localhost:8000
API docs       http://localhost:8000/docs  (when DEBUG=true)
PostgreSQL     localhost:5433
Sandbox        internal-only on port 8100
```

Compose builds the Python, JavaScript, C/C++, and Java execution images before starting the sandbox runner.

## Local LLM

The mentor uses an OpenAI-compatible API. The default configuration is compatible with the local model endpoint used by this project:

```text
LLM_BASE_URL=http://127.0.0.1:8080/v1
LLM_MODEL=auto
```

`LLM_MODEL=auto` discovers the first model returned by `/models`. If the model service is unavailable, deterministic template hints are used instead.

## Features

### Real-time analysis

- Python AST syntax analysis
- Tree-sitter error recovery
- Ruff lint/name/style checks
- stable fingerprints and deduplication
- stale-result protection with sequence numbers
- rate and concurrency limits
- latency/stage telemetry

### Execution

Code runs in a separate sandbox service with network disabled, read-only root filesystem, dropped capabilities, `no-new-privileges`, non-root execution, CPU/memory/PID/output/time limits, and an isolated executable tempfs for compiled languages.

### Mentor

H1-H3 are progressive hints without complete fenced solutions. H4 requires explicit confirmation. Secret redaction and prompt-injection-aware system instructions are applied before LLM calls.

### Screen source

Screen sharing is opt-in. Frames are processed transiently, OCR is used to detect candidate code, a confidence gate suppresses low-confidence diagnostics, and a tracked region is smoothed across frames. Manual region coordinates are available as a fallback.

### Analytics

Sessions track analysis counts, errors detected/fixed, hint usage, execution/test statistics, timing and top diagnostic categories. Completed sessions are retained only for the configured retention window.

## Desktop overlay

Install the optional always-on-top companion:

```powershell
python -m venv .venv-overlay
.\.venv-overlay\Scripts\Activate.ps1
pip install -r desktop_overlay/requirements.txt
python desktop_overlay/app.py --server http://127.0.0.1:8000 --language python --watch
```

When no session token is supplied, the overlay creates one through the API.

Hotkeys:

```text
F8 = read screen now
F9 = request H1
```

## Validation

Backend:

```bash
cd backend
uv sync
uv run ruff check .
uv run ruff format --check .
uv run mypy .
uv run pytest
```

Frontend:

```bash
cd frontend
pnpm install --frozen-lockfile
pnpm lint
pnpm typecheck
pnpm test --run
pnpm build
pnpm exec playwright install --with-deps
pnpm e2e
```

Sandbox:

```bash
cd sandbox
uv sync
uv run pytest tests -m "isolation or limits"
```

## Important security boundary

The sandbox runner is the only component allowed to access Docker. This is a deliberate local/dev architecture. Because that runner has the Docker socket, it must be treated as a privileged infrastructure component. A public multi-tenant deployment should move execution into a stronger boundary such as a dedicated VM or equivalent isolated runtime.

## Project structure

```text
backend/app/
  analysis/       AST, Tree-sitter, Ruff, taxonomy, aggregation
  api/            sessions, problems, execution, mentor, analytics, screen
  execution/      API-to-sandbox client and test orchestration
  mentor/         prompts, templates, adaptation, LLM client
  persistence/    database/session history/retention
  vision/         OCR, code-region detection and tracking
  ws/             real-time WebSocket service

frontend/src/
  components/     editor, diagnostics, problems, analytics, screen, mentor
  services/       API and WebSocket clients
  stores/         Zustand analysis state
  types/          wire/editor TypeScript contracts
  e2e/            Playwright smoke tests

sandbox/
  images/         Python, JavaScript, C/C++, Java runtime images
  runner/         privileged execution gateway

desktop_overlay/  optional OS-level always-on-top mentor
eval/             evaluation datasets and benchmarks
docs/             architecture, status and operational documentation
```
