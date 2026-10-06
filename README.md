# AI Real-Time Coding Screener / AI Coding Mentor

A web application that watches learner code as it's written, finds syntax, runtime, logic and quality problems with real tools (parsers, linters, sandboxed execution, test cases), and uses an LLM to turn verified findings into progressive hints.

## Status

✅ **Current state: Phase 2 — Fast Static Analysis implemented.** The live MVP is a React/Monaco frontend connected to a FastAPI WebSocket analysis pipeline using Tree-sitter, Python AST checks, and Ruff. Sandbox execution, persistence, LLM mentoring, and screen/OCR capture remain deferred phases.

## Quick Start

### Prerequisites

- Docker with Docker Compose
- Node.js 24 LTS and pnpm 11
- Python 3.11+ and uv
- Git
- LM Studio (for local LLM)

### Setup

1. **Clone and setup environment:**
   ```bash
   git clone <repository-url>
   cd ai-coding-mentor
   cp .env.example .env
   # Edit .env with your configuration
   ```

2. **Start the database:**
   ```bash
   make db-up
   ```

3. **Setup backend:**
   ```bash
   cd backend
   uv sync
   ```

4. **Setup frontend:**
   ```bash
   cd frontend
   pnpm install
   ```


### Development

Run the development servers:
```bash
# Terminal 1: Backend
make dev-backend

# Terminal 2: Frontend  
make dev-frontend

# Terminal 3: Database (if not already running)
make db-up
```

Visit http://localhost:5173 to access the application.

## Architecture

- **Backend (live)**: FastAPI + WebSocket + Tree-sitter + Python AST + Ruff
- **Frontend (live)**: React + Vite + Monaco Editor + Zustand + WebSocket client
- **Database**: PostgreSQL infrastructure is present but persistence is not on the live Phase 2 path
- **Deferred**: sandboxed execution, LLM mentoring, persistence/learner record, screen/OCR source

## Available Commands

| Command | Description |
|---------|-------------|
| `make check` | Lint, format check and type-check |
| `make test` | Run the currently implemented backend and frontend tests |
| `make db-up` | Start PostgreSQL database |
| `make dev-backend` | Start backend development server |
| `make dev-frontend` | Start frontend development server |


See the [Dependencies and Commands](docs/06-DEPENDENCIES-AND-COMMANDS.md) document for complete details.

## Project Structure

```
ai-coding-mentor/
├── backend/          # FastAPI backend
├── frontend/         # React frontend  
├── sandbox/          # Code execution sandbox
├── docs/            # Project documentation
└── eval/            # Evaluation and benchmarks
```

## Safety

- The live Phase 2 path performs static analysis only; it does not execute learner code.
- Sandbox execution is a deferred Phase 3 capability and is not started by the current Compose stack.
- No screen frames are captured by the live Phase 2 app.
- Progressive hints/LLM behavior is deferred to Phase 4.

## Documentation

- [Project Brief](docs/00-PROJECT-BRIEF.md) - Goals, scope, constraints
- [Architecture](docs/03-ARCHITECTURE.md) - Components, flows, contracts
- [Implementation Plan](docs/05-IMPLEMENTATION-PLAN.md) - Phases and steps
- [Dependencies](docs/06-DEPENDENCIES-AND-COMMANDS.md) - Tools and commands

## License

Private development project.