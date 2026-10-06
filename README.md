# AI Real-Time Coding Screener / AI Coding Mentor

A web application that watches learner code as it is written, finds syntax, runtime,
logic and quality problems with real tools (parsers, linters, sandboxed execution,
test cases), and uses an LLM to turn those **verified** findings into progressive,
guard-railed hints. It never hands over the full solution unless the learner
explicitly asks at the last level (H4), after H1–H3 and a confirmation click.

**Status: phases 0–9 complete.** Fast static analysis, sandboxed execution, the
mentor engine, persistence, analytics, screen-capture analysis and the release
hardening are built, tested and documented. Evidence for every success criterion
is in `docs/11-FINAL-CHECKLIST.md`; measured numbers are in *Verification* below.

---

## What it does

| Capability | Where |
|---|---|
| Real-time typing analysis over WebSocket (syntax, lint, quality) | `backend/app/analysis/` |
| Sandboxed execution with runtime-error mapping and test cases | `sandbox/`, `backend/app/execution/` |
| Progressive H1–H4 hints with guardrails and template fallback | `backend/app/mentor/` |
| Learner record: sessions, issues, hints, delete-my-data | `backend/app/learner/`, `backend/app/api/history.py` |
| Progress analytics and rule-based adaptation | `backend/app/api/progress.py`, `backend/app/learner/adaptation.py` |
| Screen capture with automatic code-region discovery + OCR | `backend/app/vision/`, `frontend/src/features/capture/` |

## Architecture in one screen

```
Editor / Screen  ──►  Frontend (React + Vite)
                          │  WS: code_update        │  REST: hints, progress, history, capture
                          ▼                        ▼
                   Backend API (FastAPI)
                     ├── analysis pipeline  →  Tree-sitter + Python AST + Ruff  (concurrent, non-blocking)
                     ├── mentor engine      →  trigger → prompt → LLM → guardrails → hint
                     ├── learner record     →  PostgreSQL (SQLAlchemy async + Alembic)
                     └── vision pipeline    →  region detect / track → OCR → reconstruct (confidence-gated)
                          │
                          ▼
                   Sandbox runner (separate container, no network, non-root)
```

**Trust boundary:** learner code is untrusted and only ever runs inside `sandbox/`.
It is never `exec`'d in the API process, and the API container never gets the
Docker socket. Learner code, OCR text and detected regions are **data, not
instructions**, inside prompts; the mentor LLM has no tools.

## Quick start (local, single user)

```bash
# 1. Configuration — copy the template, then fill in provider keys if you want
#    LLM-backed hints. Template-only mode works with no keys at all.
cp .env.example .env

# 2. Install dependencies
make install-deps

# 3. Database (PostgreSQL 15 in Docker, host port 5433)
make db-up
make db-migrate

# 4. Run the two dev servers (separate terminals)
make dev-backend     # http://localhost:8000  (docs at /docs when DEBUG=true)
make dev-frontend    # http://localhost:5173
```

Optional, for running learner code safely (required for the Run panel):

```bash
make sandbox-build   # builds the Python sandbox image
```

Everything also works without `make`; the plain commands are in
`docs/06-DEPENDENCIES-AND-COMMANDS.md`.

### Hints without an LLM

`LLM_ENABLED=false` (the default) gives deterministic template hints for H1–H3.
Set `LLM_ENABLED=true` plus `LLM_BASE_URL` / `LLM_MODEL` / `LLM_API_KEY` to use a
local (LM Studio, Ollama, vLLM) or hosted OpenAI-compatible endpoint. H4 always
requires the LLM, because a template cannot know the learner's actual solution.

## Configuration

The app reads `.env` from the repository root (and `backend/.env` if present).
Every variable is documented in `.env.example`. The ones that matter most:

| Variable | Default | Effect |
|---|---|---|
| `LLM_ENABLED` | `false` | Enables LLM-backed hints; false = template-only |
| `FEATURE_SCREEN_SOURCE` | `false` | Enables the screen-capture pipeline (off by default) |
| `EXECUTION_ENABLED` | `true` | Kill switch for the sandbox runner |
| `STORE_CODE_TEXT` | `true` | Store redacted code at checkpoints; false stores no code |
| `DATABASE_URL` | — | PostgreSQL DSN (compose default: `localhost:5433/mentor`) |
| `CORS_ORIGINS` | localhost:3000,5173 | Comma-separated allowed origins |

**Never commit `.env`.** `.gitignore` ignores it and a security test fails if it
is ever tracked again.

## Development commands

| Command | Purpose |
|---|---|
| `make check` | Backend lint/type check + frontend lint/typecheck |
| `make test` | Backend pytest suite |
| `make test-sandbox` | Sandbox isolation and limit tests |
| `make eval` | Analysis, hints and screen evaluations |
| `make bench` | Latency benchmark against the P-02 target |
| `make db-migrate` | Apply Alembic migrations |

## Testing

```bash
cd backend && uv run pytest tests/ -q          # unit, integration, adversarial, security
cd frontend && npx tsc --noEmit && npx vite build
cd backend && uv run python ../eval/harness/run_eval.py          # analysis precision/recall
cd backend && uv run python ../eval/harness/run_hints_eval.py   # hint guardrail pass rate
cd backend && uv run python ../eval/harness/run_screen_eval.py  # region + OCR metrics
cd backend && uv run python ../eval/harness/bench_latency.py    # latency percentiles
```

## Verification (measured, 2026-10-06)

| Check | Result |
|---|---|
| Backend test suite | **111 passed** |
| Analysis eval precision / recall | **1.0 / 1.0** on the labelled corpus |
| Analysis latency | **P50 29.2 ms, P95 32.7 ms** (target P-02 < 1000 ms) |
| Hint guardrail pass rate | **100%** on generated hints; no fenced code at H1–H3 |
| Screen region detection | **precision 1.0, recall 1.0, mean IoU 0.996** |
| OCR reconstruction | **line accuracy 0.99, CER 9.2%** (synthetic dataset) |
| Dependency audit | `pip-audit`: no known vulnerabilities |
| Frontend | `tsc --noEmit` clean, production build succeeds |

Limitations worth knowing: the OCR/region numbers come from a **synthetic**
dataset (real screenshots need consent), and the OCR engine is RapidOCR because
no Tesseract binary is installed on this machine. See `docs/11-FINAL-CHECKLIST.md`
for what could not be verified locally.

## Documentation map

- `docs/00-PROJECT-BRIEF.md` — goal, scope, constraints, success criteria
- `docs/02-STATUS.md` — what is built, phase by phase
- `docs/03-ARCHITECTURE.md` — components, contracts, data model, safety design
- `docs/05-IMPLEMENTATION-PLAN.md` — phases, steps, verification, exit criteria
- `docs/11-FINAL-CHECKLIST.md` — release readiness and evidence
- `docs/adr/` — the decisions behind the build
- `docs/DEMO-SCRIPT.md` — a walkthrough for a live demo

## Safety rules (never relaxed)

1. Learner code runs **only** in the sandbox container — never in the API process.
2. No raw screen frames are persisted; logs carry hashes and lengths, never code,
   OCR text or prompts.
3. Hints at H1–H3 contain no complete solution and no fenced code (enforced in
   `backend/app/mentor/guardrails.py`, tested adversarially).
4. H4 only on an explicit learner request, after H3, with a confirmation click.
5. Low-confidence region detection or OCR produces **no** diagnostics — manual
   region selection is the fallback.
6. `.env` and secrets are never committed.
