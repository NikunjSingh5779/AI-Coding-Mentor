# ADR-0002: Blocking Questions Resolution

**Status:** Accepted  
**Date:** 2026-10-04  
**Deciders:** Project Owner  

## Context

Questions Q2-Q7 in `docs/10-OPEN-QUESTIONS.md` were blocking project start. These decisions enable immediate development while allowing future expansion.

## Decisions

### Q2: Learner Languages - Python Only
**Decision:** A - Python only for first release  
**Rationale:** Focused scope enables faster MVP. Python has excellent tooling ecosystem (AST parsing, linting, testing). Other languages can be added in Phase 8.

### Q3: Intent Source - Built-in Problem Bank  
**Decision:** B - Built-in problem bank with test cases  
**Rationale:** Enables logic error detection with verified test cases. Provides structured learning path. Free-form coding remains available as fallback.

### Q4: LLM Provider - Switchable Architecture
**Decision:** C - Both local and hosted, switchable  
**Rationale:** Flexibility for different deployment scenarios. Local for privacy/cost control, hosted for performance. Adapter pattern handles both.

### Q5: Deployment Model - Single User Local
**Decision:** A - Single user on local machine  
**Rationale:** Simplifies security model for MVP. Multi-user can be added later with user_id already in data model.

### Q6: Timeline and Team
**Decision:** 2-week prototype, solo development, 10-15 hours/week  
**Evaluation:** Portfolio demo with live coding session  
**Rationale:** Realistic scope for demonstrable MVP

### Q7: Existing Components
**Decision:** A - Start from current planning repository  
**Rationale:** Clean slate with solid architecture foundation already established

## Consequences

- **Positive:** Clear scope enables immediate development start
- **Positive:** Architecture supports future expansion (multi-language, multi-user)  
- **Risk:** Python-only limits initial user base
- **Mitigation:** Language abstraction layer designed for easy expansion

## Implementation Impact

- Phase 0: Core scaffold (backend, frontend, sandbox)
- Phase 1: Python parser and linter integration
- Phase 2: Basic problem bank with 5-10 seed problems
- Phase 3-4: LLM mentor with hint progression
- Phase 5-7: UI/UX and testing