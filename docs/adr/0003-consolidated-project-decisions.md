# ADR-0003: Consolidated Project Decisions - Ready for Development

**Status:** Accepted  
**Date:** 2026-10-04  
**Deciders:** Project Owner  

## Context

All blocking questions Q1-Q7 from `10-OPEN-QUESTIONS.md` have been resolved. This ADR consolidates all architectural decisions and confirms the project is ready to begin Phase 0 development.

## Complete Decision Matrix

### Core Architecture Decisions

| Question | Decision | Rationale | Impact |
|----------|----------|-----------|---------|
| **Q1: Code Source** | Both editor and screen capture; editor first, screen second with automatic code discovery | Maximum flexibility for different learning contexts | Phases 4 & 7; vision components |
| **Q2: Languages** | Python only for MVP | Focused scope enables faster delivery; excellent tooling ecosystem | Phase 2-3; single sandbox image |
| **Q3: Intent Source** | Built-in problem bank with test cases | Enables verified logic error detection vs. suspicions only | Phase 3; problems database |
| **Q4: LLM Provider** | Switchable: both local (LM Studio) and hosted APIs | Deployment flexibility for privacy/cost/performance tradeoffs | Phase 4; adapter pattern |
| **Q5: Users/Deployment** | Single user on local machine | Simplified security model for MVP; multi-user upgrade path preserved | Phase 5; no auth/quotas |
| **Q6: Timeline** | 2-week prototype, solo development, 10-15 hours/week, portfolio demo | Realistic scope for demonstrable MVP with live coding session | All phases; timeline |
| **Q7: Existing Assets** | Start from current planning repository | Clean slate with solid architectural foundation | Phase 0; no legacy constraints |

### Non-Blocking Defaults (Q8-Q14)

All provisional defaults accepted:
- **Q8:** English, beginner-level explanations
- **Q9:** Metrics M1-M6 from architecture
- **Q10:** Store diagnostics/metadata; code at checkpoints only; user-controlled retention
- **Q11:** Standard library only; current stable interpreter versions
- **Q12:** PostgreSQL in Docker
- **Q13:** H1-H4 hint ladder; H4 only on explicit request
- **Q14:** Response times set after Phase 4 bake-off

### Tooling Stack (D1-D10)

All defaults approved:
- **D1:** Monorepo structure (`backend/`, `frontend/`, `sandbox/`, `eval/`, `docs/`)
- **D2:** Python: uv, Ruff, pytest, pyright
- **D3:** Frontend: Vite, pnpm, Vitest, Testing Library, Playwright
- **D4:** Monaco editor via `@monaco-editor/react`
- **D5:** React Router, Zustand for state
- **D6:** SQLAlchemy 2 async, asyncpg, Alembic
- **D7:** Pydantic → JSON Schema → TypeScript contracts
- **D8:** GitHub Actions CI
- **D9:** Makefile task runner
- **D10:** Structured JSON logging

## Implementation Impact

### Immediate Phase 0 Actions
1. **Scaffold Setup**: Create monorepo structure with all tooling
2. **Environment**: Docker Compose with PostgreSQL
3. **CI/CD**: GitHub Actions with full pipeline
4. **Contracts**: Type-safe API contracts

### Phase Dependencies Resolution
- **PH1**: Walking skeleton (editor path)
- **PH2**: Python static analysis only
- **PH3**: Python sandbox with problem bank
- **PH4**: LLM mentor with adapter pattern
- **PH5**: Single-user persistence
- **PH7**: Screen capture mode (P1 priority)

### Gated Features Status
- ✅ **IN SCOPE**: Python support, problem bank, both LLM modes, screen capture
- ❌ **OUT OF SCOPE**: Multi-language, multi-user, hosted deployment

## Quality Gates

### Success Criteria
- **M1**: Real-time editor analysis working
- **M2**: Verified Python diagnostics (syntax, lint, logic)
- **M3**: Safe sandboxed execution
- **M4**: Progressive hint system (H1-H4)
- **M5**: Session persistence and progress tracking

### Safety Requirements
- Sandboxed learner code execution (never in API process)
- Secret redaction before LLM calls
- No raw screen frame persistence
- Hint guardrails (no complete solutions at H1-H3)

## Risk Mitigation

### Technical Risks
- **Resource contention**: Measure LLM + DB + sandbox together in Phase 3-4
- **OCR accuracy**: Automatic discovery with manual fallback
- **Latency**: Local-first architecture with hosted backup

### Scope Risks
- **2-week timeline**: Core path only (PH0-PH1-PH2-PH3-PH4-PH5)
- **Cut order**: Languages (PH8) → adaptation → dashboard polish → screen mode

## Next Steps

1. **Immediate**: Begin Phase 0 scaffold
2. **Week 1**: Complete PH0-PH3 (skeleton, analysis, sandbox)
3. **Week 2**: Complete PH4-PH5 (mentor, persistence) + demo prep

## Validation

This ADR resolves all blocking questions and provides complete architectural guidance for implementation. Development can proceed immediately to Phase 0 scaffold creation.