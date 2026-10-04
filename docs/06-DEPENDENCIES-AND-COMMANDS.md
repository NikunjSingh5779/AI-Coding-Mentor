# 06 — Dependencies and Commands

## 1. Version policy

This file names tools and libraries, **not versions**. Versions are resolved from each registry at scaffold time (PH0), printed, and pinned in lockfiles. That keeps the plan from carrying stale or invented version numbers. Tools such as Tree-sitter, Tailwind and shadcn/ui change their setup steps over time, so every command below is **indicative**: check the tool's current official documentation when you run it.

Adding a dependency later: check that it is actively maintained and its licence suits the project, pin it, and mention it in the phase report.

## 2. System dependencies

| Tool | Needed for | Notes |
|---|---|---|
| Git and GitHub | Version control, CI | Given |
| Docker with Compose | Database, sandbox runner and images | Given. Sandbox tests need Docker on Linux (native, or the Linux VM Docker Desktop uses) |
| Node and pnpm | Frontend | Node version follows what the current Vite requires; printed in PH0-S1 |
| Python and uv | Backend and sandbox runner | Python version per Q11 and library support; printed in PH0-S1 |
| PostgreSQL | Database | Runs as a container; Supabase-hosted is possible (Q12) |
| LM Studio | Local LLM server | In your current setup (confirm); see section 9 |
| Tesseract program | Only if the OCR bake-off picks Tesseract | Wrapper libraries need the program installed |
| VS Code | Editor for development | Given |

Default ports (provisional, all changeable): frontend dev server 5173, backend 8000, sandbox runner 8100, PostgreSQL 5432, LM Studio 1234.

## 3. Backend dependencies

| Package | Purpose | Phase | Status |
|---|---|---|---|
| fastapi | API and WebSocket | PH1 | Given |
| uvicorn (standard extras) | ASGI server with WebSocket support | PH1 | Proposed |
| pydantic, pydantic-settings | Contracts and typed configuration | PH1 | Proposed |
| structlog or standard-library JSON logging | Structured logs (D10) | PH1 | Proposed |
| tree-sitter plus per-language grammar packages | Error-tolerant parsing | PH2 | Given |
| ruff | Python linting, run as a subprocess; also a development tool | PH2 | Given |
| httpx | Runner and LLM HTTP clients, test client | PH3 | Proposed |
| sqlalchemy (async), asyncpg, alembic | ORM, driver, migrations (D6) | PH5 | Proposed |
| opencv-python-headless, numpy, pillow | Frame preprocessing (headless build suits servers) | PH7 | Given (OpenCV) |
| OCR engine package | Chosen by the bake-off | PH7 | Given (OCR) |
| radon, or Tree-sitter-based metrics | Complexity | PH6 | Optional |
| pytest, pytest-asyncio | Tests (D2) | PH0 | Proposed |
| One type checker (pyright or mypy) | Static typing (D2) | PH0 | Proposed |
| pgvector extension | Only if RAG is built | Backlog | Optional |

## 4. Frontend dependencies

| Package | Purpose | Phase | Status |
|---|---|---|---|
| react, react-dom, typescript | App | PH0 | Given |
| vite | Build tool and dev server | PH0 | Proposed |
| tailwindcss with its Vite plugin | Styling | PH0 | Given |
| shadcn/ui (copies component source; brings Radix UI, class-variance-authority, clsx, tailwind-merge, lucide-react) | Components | PH0 | Given |
| @monaco-editor/react, monaco-editor | Editor, bundled locally (D4) | PH1 | Proposed |
| react-router, zustand | Routing and state (D5) | PH1 | Proposed |
| json-schema-to-typescript | Contract types (D7) | PH1 | Proposed |
| vitest, @testing-library/react | Unit tests (D3) | PH0 | Proposed |
| playwright | End-to-end tests (D3) | PH1 | Proposed |
| shadcn/ui chart component (built on Recharts) | Dashboard charts | PH6 | Proposed |
| eslint, prettier | Quality of our own code | PH0 | Given (ESLint as dev tooling) |

## 5. Sandbox dependencies

The runner has its own `sandbox/pyproject.toml`: a small HTTP framework and either the Docker SDK for Python or the Docker command line. Images: a Python base image (PH3); a C++ toolchain and a JDK only if Q2 includes them (PH8). Base images are pinned by digest when built; images contain no secrets and no network tools beyond what the language needs.

## 6. Environment variables

All must appear in `.env.example` when introduced. Values shown are examples or provisional defaults, never secrets.

| Variable | Purpose | Example or default | Phase |
|---|---|---|---|
| `APP_ENV` | dev, test or prod | dev | PH1 |
| `LOG_LEVEL` | Log verbosity | info | PH1 |
| `ALLOWED_ORIGINS` | Origin allowlist for WebSocket and CORS | http://localhost:5173 | PH1 |
| `MAX_SNAPSHOT_BYTES`, `MAX_FRAME_BYTES`, `MAX_MESSAGE_BYTES` | Input limits (P-10) | from P-10 | PH1 |
| `VITE_API_URL`, `VITE_WS_URL` | Frontend endpoints | http://localhost:8000, ws://localhost:8000 | PH1 |
| `ENABLED_ANALYZERS` | Which fast-path analyzers run | treesitter, python_ast, ruff | PH2 |
| `ENABLED_LANGUAGES` | Learner languages offered | python | PH2 |
| `EXECUTION_ENABLED` | Kill switch for running code | true | PH3 |
| `SANDBOX_URL` | Runner address | http://localhost:8100 | PH3 |
| `SANDBOX_SECRET` | Shared secret between API and runner | generated locally, never committed | PH3 |
| `LLM_ENABLED` | Kill switch for the LLM | true | PH4 |
| `LLM_PROVIDER` | Adapter name | openai_compatible | PH4 |
| `LLM_BASE_URL` | LLM endpoint | http://localhost:1234/v1 for LM Studio | PH4 |
| `LLM_API_KEY` | Key for hosted APIs; any placeholder for LM Studio | placeholder | PH4 |
| `LLM_MODEL` | Model identifier exactly as the server lists it | UNKNOWN until the bake-off | PH4 |
| `LLM_CONTEXT_TOKENS` | Context window available to prompts (set in LM Studio or by the provider); drives the prompt token budget | UNKNOWN until the bake-off | PH4 |
| `MENTOR_PROACTIVITY_DEFAULT` | off, on_demand or proactive | on_demand (provisional) | PH4 |
| `HOSTED_LLM_BUDGET_SESSION`, `HOSTED_LLM_BUDGET_DAY` | Budgets (P-15) | unset | PH4 |
| `DATABASE_URL` | PostgreSQL connection string | postgresql+asyncpg://user:password@localhost:5432/mentor (placeholders) | PH5 |
| `AUTH_MODE` | single_user or accounts | single_user, pending Q5 | PH5 |
| `STORE_CODE_TEXT` | Keep code text in checkpoints | true, pending Q10 | PH5 |
| `RETENTION_DAYS` | How long records are kept | UNKNOWN (Q10) | PH5 |
| `ADAPTATION_ENABLED` | Rule-based hint adaptation | true | PH6 |
| `FEATURE_SCREEN_SOURCE` | Enable the screen source | false | PH7 |
| `AUTO_CODE_DISCOVERY_ENABLED` | Enable automatic code-region discovery and tracking | true when screen source is enabled | PH7 |
| `OCR_ENGINE` | OCR engine name | set after the bake-off | PH7 |
| `REGION_CONFIDENCE_GATE` | Automatic code-region confidence threshold | set after the PH7 discovery evaluation | PH7 |
| `FLOATING_MENTOR_ENABLED` | Enable the floating mentor presentation layer | true | PH4 |

## 7. Make targets (D9)

`make` is not installed on native Windows; use WSL or Git Bash, or run the plain commands in section 8. Targets are defined in PH0 and extended as phases land.

| Target | What it does | Runs |
|---|---|---|
| `make check` | Lint, format check, type-check and fast tests for both apps | Backend: Ruff, format check, type checker, pytest. Frontend: lint, typecheck, vitest |
| `make test` | All unit and integration tests (needs the database container) | Backend pytest, frontend vitest |
| `make test-sandbox` | Isolation and limit tests | Sandbox pytest, Linux with Docker |
| `make types` | Regenerate TypeScript contract types | Schema export, then json-schema-to-typescript |
| `make db-up` | Start the database container | docker compose up for the db service |
| `make db-down` | Stop it and remove its volume | docker compose down with volumes |
| `make db-migrate` | Apply migrations | Alembic upgrade |
| `make dev-backend` | Run the API with reload | uvicorn |
| `make dev-frontend` | Run the frontend dev server | pnpm dev |
| `make sandbox-build` | Build sandbox images | docker build per image |
| `make eval` | Run an evaluation suite (analysis, hints, screen-region discovery or OCR, chosen with SUITE) | Eval harness |
| `make bench` | Latency benchmark on recorded typing traces | `eval/harness/bench_latency.py` |
| `make e2e` | End-to-end tests | Playwright |

## 8. Indicative commands

```bash
# Prerequisites: print versions (PH0-S1)
git --version && docker --version && docker compose version
node --version && pnpm --version && python --version && uv --version

# Backend (run inside backend/)
uv init --name mentor-backend
uv add fastapi "uvicorn[standard]" pydantic-settings "sqlalchemy[asyncio]" asyncpg alembic httpx tree-sitter
uv add --dev pytest pytest-asyncio ruff
uv sync
uv run ruff check . && uv run ruff format --check .
uv run pytest
uv run uvicorn app.main:app --reload --port 8000
uv run alembic upgrade head
uv run alembic downgrade -1
uv run alembic revision --autogenerate -m "describe the change"

# Frontend (from the repository root)
pnpm create vite@latest frontend --template react-ts
cd frontend
pnpm add tailwindcss @tailwindcss/vite
pnpm dlx shadcn@latest init
pnpm add @monaco-editor/react monaco-editor react-router zustand
pnpm add -D vitest @testing-library/react playwright json-schema-to-typescript
pnpm dev
pnpm build

# Database and services (repository root)
docker compose up -d db
docker compose down -v

# Sandbox
docker build -t mentor-sandbox-python sandbox/images/python
(cd sandbox && uv run pytest tests)

# Branches and tags per phase
git switch -c phase/1-walking-skeleton
git tag phase-1-complete
```

A type checker (D2) is added to the backend with its own `uv add --dev` line once chosen. The frontend `typecheck`, `lint` and `test` scripts are defined in `frontend/package.json` during PH0.

## 9. Local LLM with LM Studio

1. Start the local server from LM Studio's developer or local-server view, with the model you want loaded. Set its context window in LM Studio before starting; the value is part of the PH4 bake-off.
2. Confirm it answers: `curl http://localhost:1234/v1/models`. The response lists the model identifiers.
3. Set `LLM_BASE_URL=http://localhost:1234/v1`, `LLM_MODEL=<identifier from step 2>` and any placeholder for `LLM_API_KEY` (LM Studio's local API does not require a key).
4. The server answers with the model(s) currently loaded, so load the model before starting the backend. If the model is not loaded, the mentor falls back to templates and shows a notice (see `08-ROLLBACK-AND-FAILURE-HANDLING.md`).

Which model to use is not decided here. PH4-S1 compares the models you have available on a golden hint set and records the result.
