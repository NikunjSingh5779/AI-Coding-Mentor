# AI Real-Time Coding Screener Makefile
# Provides consistent commands across development environments

.PHONY: check test types db-up db-down db-migrate dev-backend dev-frontend sandbox-build eval bench e2e clean setup help

# Default target
help:
	@echo "Available targets:"
	@echo "  check         - Lint, format check, type-check and fast tests for both apps"
	@echo "  test          - All unit and integration tests (needs database)"
	@echo "  test-sandbox  - Isolation and limit tests"
	@echo "  types         - Regenerate TypeScript contract types"
	@echo "  db-up         - Start the database container"
	@echo "  db-down       - Stop database and remove its volume"
	@echo "  db-migrate    - Apply migrations"
	@echo "  dev-backend   - Run the API with reload"
	@echo "  dev-frontend  - Run the frontend dev server"
	@echo "  sandbox-build - Build sandbox images"
	@echo "  eval          - Run evaluation suite"
	@echo "  bench         - Latency benchmark on recorded typing traces"
	@echo "  e2e           - End-to-end tests"
	@echo "  setup         - Install all dependencies"
	@echo "  clean         - Clean build artifacts and caches"

# Quality checks
check:
	@echo "Running backend checks..."
	cd backend && uv run ruff check .
	cd backend && uv run ruff format --check .
	cd backend && uv run mypy .
	cd backend && uv run pytest --maxfail=5 -x
	@echo "Running frontend checks..."
	cd frontend && pnpm lint
	cd frontend && pnpm typecheck
	cd frontend && pnpm format:check
	cd frontend && pnpm test run

# Testing
test:
	@echo "Running all tests..."
	cd backend && uv run pytest
	cd frontend && pnpm test run
	cd eval && uv run pytest harness/

test-sandbox:
	@echo "Running sandbox isolation tests..."
	cd sandbox && uv run pytest tests/

# Type generation
types:
	@echo "Generating TypeScript types from backend schemas..."
	cd backend && uv run python -c "from app.schemas.export import export_schemas; export_schemas()"
	cd frontend && pnpm json-schema-to-typescript --input ../backend/schemas.json --output src/types/generated/api.ts

# Database operations
db-up:
	docker compose up -d db

db-down:
	docker compose down -v

db-migrate:
	cd backend && uv run alembic upgrade head

# Development servers
dev-backend:
	cd backend && uv run uvicorn app.main:app --reload --port 8000

dev-frontend:
	cd frontend && pnpm dev

# Sandbox
sandbox-build:
	docker build -t mentor-sandbox-python sandbox/images/python

# Evaluation and benchmarking
eval:
	cd eval && uv run python harness/run_eval.py

bench:
	cd eval && uv run python harness/bench_latency.py

# End-to-end testing
e2e:
	cd frontend && pnpm playwright test

# Setup and maintenance
setup:
	@echo "Setting up all components..."
	cd backend && uv sync
	cd frontend && pnpm install
	cd sandbox && uv sync
	cd eval && uv sync
	@echo "Setup complete!"

clean:
	@echo "Cleaning build artifacts..."
	cd backend && rm -rf .venv __pycache__ .pytest_cache .mypy_cache .ruff_cache dist/ build/
	cd frontend && rm -rf node_modules dist .vite
	cd sandbox && rm -rf .venv __pycache__ .pytest_cache dist/ build/
	cd eval && rm -rf .venv __pycache__ .pytest_cache dist/ build/ reports/
	docker system prune -f
	@echo "Clean complete!"