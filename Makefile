"""
Complete Development Commands and Setup for AI Real-Time Coding Screener
"""

# Development commands for easy project management
.PHONY: help dev-backend dev-frontend db-up db-down test check clean install-deps setup dev-all

help: ## Show this help message
	@echo "AI Real-Time Coding Screener - Development Commands"
	@echo "=================================================="
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install-deps: ## Install all dependencies
	@echo "Installing backend dependencies..."
	cd backend && uv sync
	@echo "Installing frontend dependencies..."
	cd frontend && pnpm install --frozen-lockfile
	@echo "Installing sandbox dependencies..."
	cd sandbox && uv sync

dev-backend: ## Start FastAPI development server
	@echo "Starting AI Real-Time Coding Screener backend..."
	cd backend && uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

dev-frontend: ## Start React development server
	@echo "Starting AI Real-Time Coding Screener frontend..."
	cd frontend && pnpm dev

db-up: ## Start PostgreSQL database
	docker compose up -d db
	@echo "Database started. Connection: postgresql+asyncpg://mentor:password@localhost:5433/mentor"

db-down: ## Stop PostgreSQL database (keeps data volume)
	docker compose down db

test: ## Run all tests
	@echo "Running backend tests..."
	cd backend && python -m pytest tests/ -v
	@echo "Running frontend tests..."
	cd frontend && npm test

check: ## Run linting and type checking
	@echo "Checking backend code..."
	cd backend && python -m ruff check . && python -m mypy .
	@echo "Checking frontend code..."
	cd frontend && npm run lint && npm run typecheck

clean: ## Clean build artifacts
	@echo "Cleaning build artifacts..."
	find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
	find . -name "*.pyc" -delete 2>/dev/null || true
	cd frontend && rm -rf dist/ node_modules/.cache/ 2>/dev/null || true

# Full development setup
setup: install-deps db-up ## Complete development environment setup
	@echo "✅ AI Real-Time Coding Screener setup complete!"
	@echo ""
	@echo "🚀 To start development:"
	@echo "   Terminal 1: make dev-backend"
	@echo "   Terminal 2: make dev-frontend"
	@echo ""
	@echo "🌐 URLs:"
	@echo "   Frontend: http://localhost:5173"
	@echo "   Backend API: http://localhost:8000"
	@echo "   API Docs: http://localhost:8000/docs"

# Development with all services
dev-all: ## Start all development services
	docker-compose up -d
	@echo "All services started:"
	@echo "  - Frontend: http://localhost:5173"
	@echo "  - Backend: http://localhost:8000"
	@echo "  - Database: localhost:5433"