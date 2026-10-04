# AI Real-Time Coding Screener / AI Coding Mentor

A web application that watches learner code as it's written, finds syntax, runtime, logic and quality problems with real tools (parsers, linters, sandboxed execution, test cases), and uses an LLM to turn verified findings into progressive hints.

## Status

⚠️ **Planning Phase**: Nothing is built yet. This is the core infrastructure setup (Phase 0).

## Quick Start

### Prerequisites

- Docker with Docker Compose
- Node.js 18+ and pnpm
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
   make db-migrate
   ```

4. **Setup frontend:**
   ```bash
   cd frontend
   pnpm install
   ```

5. **Build sandbox:**
   ```bash
   make sandbox-build
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

- **Backend**: FastAPI + PostgreSQL + async event bus
- **Frontend**: React + Vite + Monaco Editor + WebSocket client
- **Sandbox**: Docker containers with hardened policies
- **LLM**: Switchable (local LM Studio + hosted APIs)

## Available Commands

| Command | Description |
|---------|-------------|
| `make check` | Lint, format check, type-check and fast tests |
| `make test` | Run all unit and integration tests |
| `make db-up` | Start PostgreSQL database |
| `make dev-backend` | Start backend development server |
| `make dev-frontend` | Start frontend development server |
| `make sandbox-build` | Build sandbox Docker images |

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

- Learner code runs only in hardened Docker containers
- No raw screen frames stored
- Secrets redacted before LLM calls
- Progressive hint system never reveals full solutions

## Documentation

- [Project Brief](docs/00-PROJECT-BRIEF.md) - Goals, scope, constraints
- [Architecture](docs/03-ARCHITECTURE.md) - Components, flows, contracts
- [Implementation Plan](docs/05-IMPLEMENTATION-PLAN.md) - Phases and steps
- [Dependencies](docs/06-DEPENDENCIES-AND-COMMANDS.md) - Tools and commands

## License

Private development project.