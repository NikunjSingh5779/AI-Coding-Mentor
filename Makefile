"""
Complete Development Commands and Setup for AI Real-Time Coding Screener
"""

# Development commands for easy project management
.PHONY: help dev-backend dev-frontend db-up sandbox-build test check clean install-deps

help: ## Show this help message
	@echo "AI Real-Time Coding Screener - Development Commands"
	@echo "=================================================="
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install-deps: ## Install all dependencies
	@echo "Installing backend dependencies..."
	cd backend && pip install -e .
	@echo "Installing frontend dependencies..."
	cd frontend && npm install
	@echo "Installing sandbox dependencies..."
	cd sandbox && pip install -e .

dev-backend: ## Start FastAPI development server
	@echo "Starting AI Real-Time Coding Screener backend..."
	cd backend && python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

dev-frontend: ## Start React development server
	@echo "Starting AI Real-Time Coding Screener frontend..."
	cd frontend && npm run dev

db-up: ## Start PostgreSQL database
	docker-compose up -d db
	@echo "Database started. Connection: postgresql://postgres:password@localhost:5432/ai_screener"

sandbox-build: ## Build Python sandbox Docker image
	@echo "Building Python sandbox..."
	cd sandbox && docker build -t ai-screener-sandbox .

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
setup: install-deps db-up sandbox-build ## Complete development environment setup
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

# Production deployment
deploy-prod: ## Deploy to production
	@echo "Deploying AI Real-Time Coding Screener to production..."
	docker-compose -f docker-compose.prod.yml up -d --build

# Development with all services
dev-all: ## Start all development services
	docker-compose up -d
	@echo "All services started:"
	@echo "  - Frontend: http://localhost:5173"
	@echo "  - Backend: http://localhost:8000"
	@echo "  - Database: localhost:5432"