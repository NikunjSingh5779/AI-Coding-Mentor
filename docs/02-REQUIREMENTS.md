# 02 — Requirements

**Requirement IDs, priorities, gates, phases**

## Functional Requirements (FR)

### Core Analysis (P0)
| ID | Requirement | Priority | Gate | Phase |
|----|-------------|----------|------|--------|
| FR-01 | Real-time syntax error detection via Tree-sitter | P0 | - | PH2 |
| FR-02 | Monaco editor integration with debounced snapshots | P0 | Q1 | PH1 |
| FR-03 | Python AST validation and compile-time error detection | P0 | Q2 | PH2 |
| FR-04 | Ruff linting integration for Python quality issues | P0 | Q2 | PH2 |
| FR-05 | C++ syntax analysis via Tree-sitter (conditional) | P1 | Q2 | PH8 |
| FR-06 | Java syntax analysis via Tree-sitter (conditional) | P1 | Q2 | PH8 |

### Execution and Testing (P0)
| ID | Requirement | Priority | Gate | Phase |
|----|-------------|----------|------|--------|
| FR-07 | Sandboxed Python code execution with security hardening | P0 | - | PH3 |
| FR-08 | Runtime error capture and diagnostic mapping | P0 | - | PH3 |
| FR-09 | Test case execution and result comparison | P0 | Q3 | PH3 |
| FR-10 | Timeout and resource limit enforcement | P0 | - | PH3 |

### Mentor System (P0)
| ID | Requirement | Priority | Gate | Phase |
|----|-------------|----------|------|--------|
| FR-11 | Progressive 4-level hint ladder (H1-H4) | P0 | Q13 | PH4 |
| FR-12 | Guardrails preventing solution leakage | P0 | - | PH4 |
| FR-13 | Trigger policy for proactive and requested hints | P0 | - | PH4 |
| FR-14 | LLM provider abstraction (local + hosted) | P0 | Q4 | PH4 |
| FR-15 | Hint caching and budget management | P0 | - | PH4 |

### Data and Analytics (P0-P1)
| ID | Requirement | Priority | Gate | Phase |
|----|-------------|----------|------|--------|
| FR-16 | Issue lifecycle tracking and fingerprinting | P0 | - | PH5 |
| FR-17 | Progress dashboard with mistake analytics | P1 | Q9 | PH6 |
| FR-18 | Adaptive hint system based on learner history | P1 | - | PH6 |

### Screen Source (P1, Q1-dependent)
| ID | Requirement | Priority | Gate | Phase |
|----|-------------|----------|------|--------|
| FR-19 | Screen capture via getDisplayMedia API | P1 | Q1 | PH7 |
| FR-20 | Automatic code region detection and tracking | P1 | Q1 | PH7 |
| FR-21 | OCR with confidence gating | P1 | Q1 | PH7 |
| FR-22 | Manual region selection fallback | P1 | Q1 | PH7 |

### Problem Bank (P0, Q3-dependent)
| ID | Requirement | Priority | Gate | Phase |
|----|-------------|----------|------|--------|
| FR-23 | Built-in problem bank with test cases | P0 | Q3 | PH3 |
| FR-24 | Hidden test case support | P0 | Q3 | PH3 |
| FR-25 | Free-form coding mode (no problem statement) | P1 | - | PH3 |

### Extensions (P2, future)
| ID | Requirement | Priority | Gate | Phase |
|----|-------------|----------|------|--------|
| FR-26 | VS Code extension integration | P2 | Q1 | Future |
| FR-27 | Floating mentor overlay positioning | P1 | Q1 | PH7 |
| FR-28 | Multi-language hint templates | P1 | Q8 | PH4 |

## Non-Functional Requirements (NFR)

### Performance (P0)
| ID | Requirement | Priority | Gate | Phase |
|----|-------------|----------|------|--------|
| NFR-01 | <1s latency from keystroke to diagnostic markers | P0 | Q14 | PH2 |
| NFR-02 | <30s LLM response time with retry logic | P0 | Q4 | PH4 |
| NFR-03 | Support for 10+ concurrent learner sessions | P1 | Q5 | PH5 |

### Security (P0)
| ID | Requirement | Priority | Gate | Phase |
|----|-------------|----------|------|--------|
| NFR-04 | No learner code execution in API process | P0 | - | PH3 |
| NFR-05 | Hardened sandbox with no network access | P0 | - | PH3 |
| NFR-06 | Origin-checked WebSocket connections | P0 | - | PH1 |
| NFR-07 | Secret redaction before LLM calls | P0 | - | PH4 |
| NFR-08 | Input validation and size limits | P0 | - | PH1 |

### Privacy (P0)
| ID | Requirement | Priority | Gate | Phase |
|----|-------------|----------|------|--------|
| NFR-09 | No raw screen frame persistence | P0 | Q1 | PH7 |
| NFR-10 | Minimal data storage with retention policy | P0 | Q10 | PH5 |
| NFR-11 | Local vs hosted LLM data flow disclosure | P0 | Q4 | PH4 |

### Reliability (P0)
| ID | Requirement | Priority | Gate | Phase |
|----|-------------|----------|------|--------|
| NFR-12 | Graceful degradation when components fail | P0 | - | PH1 |
| NFR-13 | WebSocket auto-reconnect with state recovery | P0 | - | PH1 |
| NFR-14 | Database backup and recovery procedures | P1 | Q12 | PH5 |

## System Constraints (SC)

### Technical Constraints
| ID | Constraint | Impact | Mitigation |
|----|------------|---------|------------|
| SC-01 | Browser-based deployment only | Limits system access | Use WebSocket + REST APIs |
| SC-02 | Docker required for sandbox isolation | Deployment dependency | Document installation requirements |
| SC-03 | PostgreSQL as primary database | Technology lock-in | Use SQLAlchemy for abstraction |
| SC-04 | No external network in sandbox | Limited package access | Standard library only by default |
| SC-05 | GPU memory constraints for local LLM | Model size limits | Measure and document in bake-off |

### Business Constraints
| ID | Constraint | Impact | Mitigation |
|----|------------|---------|------------|
| SC-06 | Single developer, 2-week timeline | Limited scope | Phase-gated development |
| SC-07 | Academic evaluation requirements | Must be measurable | Built-in analytics dashboard |
| SC-08 | No external hosting budget | Local deployment only | Support both local and hosted modes |

## Acceptance Criteria

### Phase 0 - Infrastructure
- [ ] `make dev-backend` starts FastAPI server
- [ ] `make dev-frontend` starts React application  
- [ ] `make sandbox-build` creates hardened Python container
- [ ] `make test` runs all test suites successfully
- [ ] WebSocket connection established between frontend and backend

### Phase 1 - Core Pipeline  
- [ ] Monaco editor captures and debounces code changes
- [ ] WebSocket delivers snapshots with sequence numbering
- [ ] Fast analysis pipeline returns diagnostics <1s
- [ ] Diagnostic markers appear in editor interface
- [ ] Session state managed with reconnection support

### Phase 2 - Analysis Tools
- [ ] Python syntax errors detected via AST and Tree-sitter
- [ ] Ruff linting integrated with taxonomy mapping
- [ ] Performance benchmark shows <1s p95 latency
- [ ] Error fingerprinting enables issue tracking
- [ ] Evaluation harness measures precision/recall

### Phase 3 - Sandbox Execution
- [ ] Python code executes in hardened Docker container
- [ ] Runtime errors mapped to diagnostic categories
- [ ] Test cases execute with pass/fail results
- [ ] Resource limits enforced (time, memory, output)
- [ ] Security isolation verified through attack tests

### Phase 4 - Mentor Engine
- [ ] 4-level hint ladder implemented with guardrails
- [ ] LLM integration supports local and hosted providers
- [ ] Trigger policy respects cooldowns and proactivity settings
- [ ] Fallback templates work when LLM unavailable
- [ ] Prompt injection resistance verified

### Phase 5 - Persistence
- [ ] Database schema supports all data models
- [ ] Issue lifecycle tracking across sessions
- [ ] Migration system with rollback capabilities
- [ ] Session history and analytics queries
- [ ] Data retention and privacy controls

### Phase 6 - Analytics
- [ ] Progress dashboard shows mistake trends
- [ ] Adaptive hints based on learner history  
- [ ] Performance metrics match direct SQL queries
- [ ] Quality metrics exported for evaluation
- [ ] Visual charts responsive across devices

### Evaluation Criteria
- **Functionality:** All P0 requirements implemented and tested
- **Performance:** <1s diagnostic latency, <30s hint generation
- **Security:** Sandbox isolation holds under attack scenarios  
- **Usability:** Learner can code and receive helpful hints
- **Reliability:** System handles failures gracefully
- **Measurability:** Analytics enable academic evaluation