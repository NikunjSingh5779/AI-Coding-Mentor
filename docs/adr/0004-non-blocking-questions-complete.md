# ADR-0004: Non-Blocking Questions Resolution - Complete Decision Matrix

**Status:** Accepted  
**Date:** 2026-10-04  
**Deciders:** Project Owner  

## Context

With blocking questions Q1-Q7 resolved, the remaining non-blocking questions Q8-Q14 and tooling defaults D1-D10 need final confirmation. All provisional defaults are accepted to enable immediate development start.

## Non-Blocking Decisions (Q8-Q14)

### Q8: Explanation Language and Reading Level
**Decision:** English, plain language for beginners
**Rationale:** Standard approach with localization framework for future expansion
**Impact:** Affects FR-10 and hint templates

### Q9: Dashboard Improvement Metrics  
**Decision:** Metrics M1-M6 from architecture specification
**Rationale:** Comprehensive coverage of learning progress indicators
**Impact:** Affects FR-17 and Phase 6 implementation

### Q10: Code Storage and Retention Policy
**Decision:** 
- Store diagnostics, issue metadata, and hint text
- Store code text only at checkpoints with secret redaction  
- User-controlled retention with delete-my-data function
- No automatic expiry (RETENTION_DAYS unset)
**Rationale:** Balances functionality needs with privacy protection
**Impact:** Affects FR-15, NFR-04, Phase 5

### Q11: Language Versions and Package Support
**Decision:** Standard library only; current stable interpreter versions
**Rationale:** Simplified sandbox environment for MVP; reduces attack surface
**Impact:** Affects Phase 2-3, Phase 8, ENV_UNSUPPORTED category

### Q12: Database Deployment  
**Decision:** PostgreSQL in Docker with standard drivers
**Rationale:** Local development simplicity; Supabase upgrade path preserved
**Impact:** Affects tooling default D6 and Phase 5

### Q13: Hint Ladder and Solution Reveal Rules
**Decision:** 
- H1-H4 progressive hint system from architecture
- H4 (complete solution) only on explicit request after H3
- No automatic escalation based on failed attempts
**Rationale:** Maintains learning value; prevents solution shortcuts
**Impact:** Affects FR-11 and mentor guardrails

### Q14: Response Time Requirements
**Decision:** 
- P-02 target for static analysis markers
- Mentor response time set after Phase 4 LLM bake-off
- No hard requirements for MVP evaluation
**Rationale:** Performance optimization based on actual measurements
**Impact:** Affects NFR-01, NFR-02

## Tooling Stack Confirmation (D1-D10)

All tooling defaults **APPROVED** for immediate implementation:

| ID | Component | Decision | Rationale |
|---|---|---|---|
| D1 | Repository Structure | Monorepo: `backend/`, `frontend/`, `sandbox/`, `eval/`, `docs/` | Separate toolchains, unified codebase |
| D2 | Python Tooling | uv, Ruff, pytest + pytest-asyncio, pyright | Modern, fast toolchain |
| D3 | Frontend Tooling | Vite, pnpm, Vitest, Testing Library, Playwright | Standard React ecosystem |
| D4 | Code Editor | Monaco via `@monaco-editor/react` | Offline capability, CSP compliance |
| D5 | State Management | React Router + Zustand | Lightweight, sufficient for scope |
| D6 | Database Stack | SQLAlchemy 2 async + asyncpg + Alembic | Modern async Python data layer |
| D7 | Type Safety | Pydantic → JSON Schema → TypeScript | Single source of truth for contracts |
| D8 | CI/CD | GitHub Actions | Integrated with existing workflow |
| D9 | Task Runner | Makefile with documented plain commands | Cross-platform compatibility |
| D10 | Observability | Structured JSON logging with correlation IDs | Performance monitoring capability |

## Implementation Readiness

### Phase 0 Ready to Begin
All architectural decisions resolved:
- ✅ Code source strategy (editor + screen with auto-discovery)
- ✅ Language support (Python-focused MVP)
- ✅ Logic error detection (problem bank with test cases) 
- ✅ LLM architecture (switchable local/hosted)
- ✅ Deployment model (single-user local)
- ✅ Timeline and evaluation (2-week prototype, portfolio demo)
- ✅ Technology stack (complete tooling matrix)

### Gated Features Matrix
Based on resolved decisions:

| Feature Category | Status | Phase |
|---|---|---|
| **Core MVP** | ✅ IN SCOPE | PH0-PH5 |
| Python static analysis | ✅ IN SCOPE | PH2 |
| Sandboxed execution | ✅ IN SCOPE | PH3 |
| Problem bank with tests | ✅ IN SCOPE | PH3 |
| Progressive hint system | ✅ IN SCOPE | PH4 |
| Session persistence | ✅ IN SCOPE | PH5 |
| **Extended Features** | 📋 PLANNED | PH6-PH8 |
| Screen capture mode | 📋 P1 PRIORITY | PH7 |
| Multi-language support | 📋 P1 PRIORITY | PH8 |
| Analytics dashboard | 📋 P1 PRIORITY | PH6 |
| **Out of Scope** | ❌ EXCLUDED | - |
| Multi-user deployment | ❌ Future upgrade | - |
| Authentication system | ❌ Not needed for MVP | - |
| Hosted infrastructure | ❌ Local-first approach | - |

## Success Criteria Confirmation

### Technical Milestones
- **M1**: Real-time editor analysis (skeleton alive)
- **M2**: Verified Python diagnostics (real markers) 
- **M3**: Safe sandboxed execution (safe to run)
- **M4**: Progressive mentoring system (mentor demo)
- **M5**: Progress tracking (learner records)

### Quality Gates
- All sandbox isolation tests pass
- Hint guardrails enforce H1-H3 limitations
- Secret redaction before all LLM calls
- No complete solutions below H4 level

## Risk Mitigation Strategies

### Timeline Risks (2-week constraint)
- **Cut order**: Additional languages → adaptation features → dashboard polish → screen mode
- **Core path priority**: PH0→PH1→PH2→PH3→PH4→PH5 (essential MVP)
- **Optional branches**: PH6, PH7, PH8 can be deferred

### Technical Risks  
- **Resource contention**: Measure LLM + DB + sandbox performance in PH3-4
- **OCR accuracy**: Auto-discovery with manual selection fallback
- **Integration complexity**: Incremental validation at each phase

## Next Actions

### Immediate (Phase 0)
1. **Repository scaffold**: Create monorepo structure with all tooling
2. **Development environment**: Docker Compose + PostgreSQL setup
3. **CI/CD pipeline**: GitHub Actions with comprehensive checks
4. **Contract system**: Pydantic → TypeScript type generation

### Week 1 Target (Phases 1-3)
1. **Walking skeleton**: Real-time editor with placeholder analysis
2. **Python analysis**: AST parsing, linting, syntax checking
3. **Sandbox runner**: Safe code execution with problem bank

### Week 2 Target (Phases 4-5)
1. **Mentor engine**: LLM integration with progressive hints
2. **Persistence layer**: Session history and learner progress
3. **Demo preparation**: End-to-end scenarios S1-S6

## Validation

This ADR completes the decision matrix and confirms the project is fully ready for development. All architectural uncertainty has been resolved with documented, traceable decisions.

**Development Status**: ✅ **CLEARED FOR IMPLEMENTATION**