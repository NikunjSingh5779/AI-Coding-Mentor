# Dependencies and Commands

## Full local stack

Prerequisites:

- Docker Desktop + Compose
- Node.js 24+
- pnpm 11+
- Python 3.11+
- uv
- Git
- Optional local OpenAI-compatible model server for AI mentoring
- Tesseract installed by the backend Docker image for screen OCR

Copy `.env.example` to `.env`, then:

```bash
docker compose up --build
```

Open `http://localhost:5173`.

Services:

```text
frontend:  5173
backend:   8000
postgres:  5433
sandbox:   internal 8100
```

The Compose build creates the Python, JavaScript, C/C++, and Java sandbox images first.

## Backend development

```bash
cd backend
uv sync
uv run ruff check .
uv run ruff format --check .
uv run mypy .
uv run pytest
uv run uvicorn app.main:app --reload --port 8000
```

## Frontend development

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

## Sandbox validation

```bash
cd sandbox
uv sync
uv run pytest tests -m "isolation or limits"
```

For the runtime smoke tests, first build the Python image:

```bash
docker build -t coding-mentor-python:ci sandbox/images/python
```

## Optional desktop floating mentor

```powershell
python -m venv .venv-overlay
.\.venv-overlay\Scripts\Activate.ps1
pip install -r desktop_overlay/requirements.txt
python desktop_overlay/app.py --server http://127.0.0.1:8000 --language python --watch
```

The overlay creates a session automatically when no token is supplied. It is frameless, always-on-top, draggable, has a context menu, and supports F8 (read now) and F9 (H1).

## Local model

The mentor speaks OpenAI-compatible HTTP. For a local server:

```text
LLM_BASE_URL=http://127.0.0.1:8080/v1
LLM_MODEL=auto
LLM_API_KEY=none
```

The model is discovered from `GET /v1/models` when `LLM_MODEL=auto`.

## Kill switches

```text
EXECUTION_ENABLED=false
LLM_ENABLED=false
FEATURE_SCREEN_SOURCE=false
AUTO_CODE_DISCOVERY_ENABLED=false
FLOATING_MENTOR_ENABLED=false
STORE_CODE_TEXT=false
```

These allow risky/optional subsystems to be disabled without changing application code.

## Production warning

The sandbox runner has the Docker socket. Keep it isolated from the public network and prefer a stronger execution boundary for multi-tenant deployments.
