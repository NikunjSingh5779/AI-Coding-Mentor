# Phase 1 Implementation Plan: Real-Time Analysis Pipeline

**Status:** Ready to Start  
**Branch:** `phase/1-real-time-pipeline`  
**Dependencies:** Phase 0 Complete ✅  
**Priority:** P0 (Critical Path)  
**Estimated Effort:** Medium (M)

## Executive Summary

Phase 1 implements the core real-time code analysis pipeline that watches learner code as it's written, detects problems with verification tools (parsers, linters, sandboxed execution), and displays diagnostic markers in the Monaco editor. This is the "walking skeleton" that proves the end-to-end flow works.

## Goals

1. **Real-time WebSocket Pipeline**: Bi-directional communication between frontend editor and backend analysis engine
2. **Python Code Analysis**: Syntax checking, AST parsing, basic linting, and quality metrics
3. **Monaco Integration**: Display diagnostic markers with severity levels and hover information
4. **Performance Target**: <1s from keystroke to diagnostic markers in editor
5. **Graceful Degradation**: System works even when components fail

## Success Criteria

- [ ] Type Python code in Monaco editor, see syntax errors within 1 second
- [ ] WebSocket connection establishes on page load and recovers from disconnects
- [ ] Diagnostic markers appear at correct line/column positions
- [ ] Hover over markers shows detailed error messages
- [ ] Backend processes at least 10 code updates per second
- [ ] All Phase 1 tests passing (unit + integration)

## Architecture Overview

```
┌─────────────────┐         WebSocket          ┌──────────────────┐
│  Monaco Editor  │ ◄────────────────────────► │   FastAPI WS     │
│   (Frontend)    │    {code, session, seq}    │    Endpoint      │
└─────────────────┘                             └──────────────────┘
                                                         │
                                                         ▼
                                                ┌──────────────────┐
                                                │  Event Bus       │
                                                │  (In-Memory)     │
                                                └──────────────────┘
                                                         │
                                                         ▼
                                                ┌──────────────────┐
                                                │ Python Analyzer  │
                                                │ - AST Parser     │
                                                │ - Syntax Check   │
                                                │ - Linting        │
                                                └──────────────────┘
                                                         │
                                                         ▼
                                                ┌──────────────────┐
                                                │  Diagnostics     │
                                                │  (JSON Array)    │
                                                └──────────────────┘
```

## Phase 1 Components

### 1. Backend Components

#### 1.1 WebSocket Endpoint (`backend/app/ws/endpoint.py`)
- **Status**: Stub exists, needs full implementation
- **Features**:
  - Connection management with origin validation
  - Session token authentication
  - Message sequencing and deduplication
  - Heartbeat/keepalive (30s interval)
  - Reconnection handling with state recovery
  - Error handling and graceful degradation

#### 1.2 Python Code Analyzer (`backend/app/analysis/python_analyzer.py`)
- **Status**: Partial implementation exists, needs completion
- **Capabilities**:
  - **Syntax Analysis**: AST parsing with error recovery
  - **Semantic Checks**: Undefined variables, unused imports, type mismatches
  - **Style Linting**: PEP 8 violations, naming conventions
  - **Quality Metrics**: Complexity, maintainability index
  - **Performance**: <100ms for typical code snippets (<500 lines)

#### 1.3 Event Bus (`backend/app/core/events.py`)
- **Status**: Basic implementation exists
- **Enhancements Needed**:
  - Priority queues for urgent vs. background tasks
  - Rate limiting per session
  - Event coalescing (debounce rapid keystrokes)
  - Metrics collection (latency, throughput)

#### 1.4 Analysis Controller (`backend/app/controllers/analysis_controller.py`)
- **Status**: Exists but needs WebSocket integration
- **Responsibilities**:
  - Receive code from WebSocket
  - Coordinate with analyzer
  - Format diagnostics for frontend
  - Track analysis metrics

### 2. Frontend Components

#### 2.1 Monaco Editor Integration (`frontend/src/components/CodeEditor.tsx`)
- **Features**:
  - Monaco editor instance with Python syntax highlighting
  - Configurable theme (VS Dark/Light)
  - Line numbers, minimap, auto-completion
  - Diagnostic marker rendering
  - Hover provider for detailed error messages
  - Keyboard shortcuts (Ctrl+S for manual analysis)

#### 2.2 WebSocket Client (`frontend/src/services/websocket.ts`)
- **Features**:
  - Connection lifecycle management
  - Automatic reconnection with exponential backoff
  - Message queuing during disconnection
  - Sequence number tracking
  - Heartbeat handling
  - TypeScript types for all messages

#### 2.3 Analysis State Management (`frontend/src/stores/analysisStore.ts`)
- **Using**: Zustand for lightweight state
- **State**:
  - Current diagnostics array
  - Connection status
  - Last analysis timestamp
  - Error states
  - Session metadata

#### 2.4 Diagnostic Display (`frontend/src/components/DiagnosticPanel.tsx`)
- **Features**:
  - List view of all diagnostics
  - Filter by severity (error, warning, info)
  - Click to jump to line in editor
  - Clear all button
  - Real-time updates

### 3. Contracts & Types

#### 3.1 WebSocket Message Formats

**Client → Server (Code Update)**
```json
{
  "type": "code_update",
  "sequence": 123,
  "session_token": "abc-xyz-789",
  "code": "def hello():\n    print('world')",
  "language": "python",
  "timestamp": "2026-10-04T16:54:52.903Z"
}
```

**Server → Client (Analysis Result)**
```json
{
  "type": "analysis_result",
  "sequence": 123,
  "session_token": "abc-xyz-789",
  "diagnostics": [
    {
      "severity": "error",
      "line": 2,
      "column": 5,
      "end_line": 2,
      "end_column": 10,
      "message": "Undefined name 'prnt'",
      "code": "F821",
      "source": "flake8"
    }
  ],
  "analysis_time_ms": 45,
  "timestamp": "2026-10-04T16:54:52.950Z"
}
```

**Heartbeat (Bidirectional)**
```json
{
  "type": "ping",
  "timestamp": "2026-10-04T16:54:52.903Z"
}
```

#### 3.2 Diagnostic Schema
```typescript
interface Diagnostic {
  severity: 'error' | 'warning' | 'info' | 'hint';
  line: number;           // 1-indexed
  column: number;         // 0-indexed
  end_line?: number;
  end_column?: number;
  message: string;
  code?: string;          // e.g., "E501" for line too long
  source?: string;        // e.g., "ruff", "pyflakes"
  fix?: {
    title: string;
    edits: Array<{
      line: number;
      column: number;
      end_line: number;
      end_column: number;
      new_text: string;
    }>;
  };
}
```

## Implementation Steps

### Step 1: Complete Backend Analysis Pipeline (Days 1-2)

**Tasks**:
1. Enhance `python_analyzer.py` with comprehensive checks
2. Add proper error recovery for partial/invalid code
3. Implement rate limiting and debouncing
4. Add performance instrumentation
5. Write unit tests for analyzer (80%+ coverage)

**Verification**:
```bash
cd backend
uv run pytest tests/test_python_analyzer.py -v
uv run python -m app.analysis.python_analyzer --test
```

**Files**:
- `backend/app/analysis/python_analyzer.py` (enhance)
- `backend/tests/test_python_analyzer.py` (create)
- `backend/app/analysis/__init__.py` (create if missing)

### Step 2: Implement WebSocket Contract (Days 2-3)

**Tasks**:
1. Complete `backend/app/ws/endpoint.py` with full contract
2. Add session validation and origin checking
3. Implement message sequencing and deduplication
4. Add heartbeat mechanism
5. Write WebSocket integration tests

**Verification**:
```bash
# Terminal 1: Start backend
cd backend && uv run uvicorn app.main:app --reload

# Terminal 2: Test WebSocket
wscat -c ws://localhost:8000/ws/code-analysis?session_token=test-123
```

**Files**:
- `backend/app/ws/endpoint.py` (complete)
- `backend/tests/test_websocket.py` (create)

### Step 3: Frontend Editor Integration (Days 3-4)

**Tasks**:
1. Create Monaco editor component with full configuration
2. Implement diagnostic marker rendering
3. Add hover provider for error details
4. Create diagnostic panel UI
5. Write component tests

**Verification**:
```bash
cd frontend
pnpm test src/components/CodeEditor.test.tsx
pnpm dev  # Manual testing
```

**Files**:
- `frontend/src/components/CodeEditor.tsx` (create)
- `frontend/src/components/DiagnosticPanel.tsx` (create)
- `frontend/src/components/CodeEditor.test.tsx` (create)
- `frontend/src/styles/editor.css` (create)

### Step 4: WebSocket Client & State Management (Days 4-5)

**Tasks**:
1. Implement WebSocket client with reconnection
2. Create Zustand store for analysis state
3. Add message queuing during disconnection
4. Implement exponential backoff for reconnection
5. Add connection status UI indicator
6. Write integration tests

**Verification**:
```bash
cd frontend
pnpm test src/services/websocket.test.ts
pnpm test src/stores/analysisStore.test.ts
```

**Files**:
- `frontend/src/services/websocket.ts` (create)
- `frontend/src/stores/analysisStore.ts` (create)
- `frontend/src/types/analysis.ts` (create)
- `frontend/src/services/websocket.test.ts` (create)

### Step 5: End-to-End Integration & Testing (Days 5-6)

**Tasks**:
1. Wire all components together
2. Add performance monitoring
3. Test reconnection scenarios
4. Verify 1-second latency target
5. Write E2E tests with Playwright
6. Load testing (simulate 10 concurrent sessions)

**Verification**:
```bash
# Start both services
docker compose up -d db
cd backend && uv run uvicorn app.main:app --reload &
cd frontend && pnpm dev &

# Run E2E tests
cd frontend && pnpm test:e2e

# Performance test
cd backend && uv run pytest tests/test_performance.py
```

**Files**:
- `frontend/tests/e2e/analysis-flow.spec.ts` (create)
- `backend/tests/test_performance.py` (create)
- `docs/performance-baseline.md` (create)

### Step 6: Documentation & Phase Report (Day 6)

**Tasks**:
1. Update API documentation
2. Add architecture diagrams
3. Document WebSocket protocol
4. Write Phase 1 completion report
5. Update `docs/02-STATUS.md`
6. Update `docs/11-FINAL-CHECKLIST.md`

**Files**:
- `docs/api/websocket-protocol.md` (create)
- `docs/performance-baseline.md` (complete)
- `docs/PHASE-1-REPORT.md` (create)
- `docs/02-STATUS.md` (update)

## Performance Targets

| Metric | Target | Measurement Method |
|--------|--------|-------------------|
| **Analysis Latency** | <100ms (p95) | Backend instrumentation |
| **End-to-End Latency** | <1s (p95) | Frontend timestamp delta |
| **Throughput** | 10 updates/sec/session | Load testing |
| **WebSocket Reconnect** | <5s | Manual testing |
| **Memory Usage** | <200MB backend | Process monitoring |
| **CPU Usage** | <30% single core | Process monitoring |

## Testing Strategy

### Unit Tests
- **Backend**: 80%+ code coverage for analyzer
- **Frontend**: All components with React Testing Library
- **Focus**: Edge cases, error handling, boundary conditions

### Integration Tests
- WebSocket connection lifecycle
- Code → Analysis → Diagnostics flow
- Reconnection with state recovery
- Multiple concurrent sessions

### E2E Tests (Playwright)
1. Load editor, type code, see markers
2. Introduce syntax error, verify marker appears
3. Fix error, verify marker disappears
4. Disconnect network, reconnect, verify recovery
5. Open multiple tabs, verify independent sessions

### Performance Tests
- Baseline latency measurement
- Load testing (10 concurrent users)
- Memory leak detection (24hr soak test)
- Network condition simulation (3G, packet loss)

## Risk Mitigation

| Risk | Impact | Mitigation |
|------|--------|------------|
| **WebSocket connection instability** | High | Automatic reconnection, message queuing, state recovery |
| **Analysis latency exceeds 1s** | High | Debouncing, incremental parsing, performance profiling |
| **Monaco bundle size too large** | Medium | Code splitting, lazy loading, CDN caching |
| **Browser compatibility issues** | Medium | Polyfills, feature detection, graceful degradation |
| **Race conditions in state** | Medium | Sequence numbers, idempotency, conflict resolution |

## Dependencies

### New Backend Dependencies
```toml
# Already in pyproject.toml from Phase 0
fastapi = "*"
uvicorn = { extras = ["standard"], version = "*" }
websockets = "*"  # Add if not present
```

### New Frontend Dependencies
```json
{
  "@monaco-editor/react": "^4.6.0",
  "monaco-editor": "^0.45.0",
  "zustand": "^4.4.7"
}
```

All versions to be pinned at installation time.

## Exit Criteria

Phase 1 is complete when:

1. ✅ All unit tests passing (80%+ coverage)
2. ✅ All integration tests passing
3. ✅ E2E test suite passing (5+ scenarios)
4. ✅ Performance targets met (documented)
5. ✅ WebSocket reconnection working reliably
6. ✅ Monaco editor displays diagnostics correctly
7. ✅ Code formatted and linted (no errors)
8. ✅ Documentation complete (API, architecture)
9. ✅ Phase report written with metrics
10. ✅ Demo recorded (30-60 second screencast)

## Rollback Procedure

If Phase 1 must be rolled back:

1. `git checkout main`
2. `git tag phase-1-rollback-$(date +%Y%m%d-%H%M%S)`
3. `git branch -D phase/1-real-time-pipeline`
4. Restart services: `docker compose restart`
5. Verify Phase 0 still works
6. Document rollback reason in `docs/08-ROLLBACK-AND-FAILURE-HANDLING.md`

## Next Phase Preview

**Phase 2: Fast Static Analysis**
- Tree-sitter integration for error-tolerant parsing
- Ruff integration for comprehensive linting
- Quality metrics (cyclomatic complexity, maintainability)
- Multi-language support preparation
- Performance optimization (<50ms analysis time)

---

**Prepared by:** Claude Code  
**Date:** 2026-10-04  
**Approver:** [Awaiting confirmation to proceed]
