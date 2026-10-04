# ICM Layer Index - AI Real-Time Coding Screener

**Infrastructure-Component-Module Documentation Catalog**

## Purpose
The ICM layer provides navigation and context for the AI Real-Time Coding Screener project. It organizes planning documents, architecture decisions, and implementation guides so developers (human or AI) can quickly find what they need.

## Document Structure

### Planning & Context (Read First)
| Document | Purpose | Status |
|----------|---------|--------|
| `00-PROJECT-BRIEF.md` | Project goal, scope, constraints, success criteria | ✅ Complete |
| `01-STACK-AND-ABSTRACT-REVIEW.md` | Technology stack validation and risk assessment | ✅ Complete |
| `02-STATUS.md` | Current project state and phase progress | 🔄 Active |
| `02-REQUIREMENTS.md` | Functional and non-functional requirements with priorities | ✅ Complete |

### Architecture & Design
| Document | Purpose | Status |
|----------|---------|--------|
| `03-ARCHITECTURE.md` | System components, data flow, contracts, security design | ✅ Complete |
| `04-FOLDER-STRUCTURE.md` | Repository layout, naming conventions, dependency rules | ✅ Complete |

### Implementation Guides
| Document | Purpose | Status |
|----------|---------|--------|
| `05-IMPLEMENTATION-PLAN.md` | Phase-by-phase implementation steps with verification | ✅ Complete |
| `06-DEPENDENCIES-AND-COMMANDS.md` | Package versions, environment variables, development commands | ✅ Complete |
| `07-TESTING-AND-VALIDATION.md` | Test suites, acceptance scenarios, traceability matrix | ✅ Complete |

### Risk & Recovery
| Document | Purpose | Status |
|----------|---------|--------|
| `08-ROLLBACK-AND-FAILURE-HANDLING.md` | Phase rollback procedures and failure modes | ✅ Complete |
| `09-RISKS-AND-EDGE-CASES.md` | Risk register and edge case catalog | ✅ Complete |

### Decision Tracking
| Document | Purpose | Status |
|----------|---------|--------|
| `10-OPEN-QUESTIONS.md` | Blocking questions, provisional defaults, decision log | ✅ Resolved |
| `adr/` | Architecture Decision Records (ADRs) | 🔄 Active |

### Quality Assurance
| Document | Purpose | Status |
|----------|---------|--------|
| `11-FINAL-CHECKLIST.md` | Release readiness and phase-exit checklists | ✅ Complete |
| `12-REVIEW-LOG.md` | Review cycles and feedback incorporation | ✅ Complete |

## Quick Navigation

### For New Developers
1. Start with `00-PROJECT-BRIEF.md` to understand the goal
2. Read `02-STATUS.md` to see current state
3. Review `03-ARCHITECTURE.md` for system design
4. Check `05-IMPLEMENTATION-PLAN.md` for current phase tasks

### For Implementation
1. Check `02-STATUS.md` for current phase
2. Read relevant phase section in `05-IMPLEMENTATION-PLAN.md`
3. Reference `04-FOLDER-STRUCTURE.md` for file locations
4. Follow `06-DEPENDENCIES-AND-COMMANDS.md` for setup

### For Decision Making
1. Check `10-OPEN-QUESTIONS.md` for resolved decisions
2. Review `adr/` for architecture decisions
3. Consult `09-RISKS-AND-EDGE-CASES.md` for known risks

### For Testing
1. Reference `07-TESTING-AND-VALIDATION.md` for test strategy
2. Check `02-REQUIREMENTS.md` for acceptance criteria
3. Review `11-FINAL-CHECKLIST.md` for phase gates

## Architecture Decision Records

| ADR | Title | Status |
|-----|-------|--------|
| ADR-0001 | Screen source and automatic code discovery | ✅ Accepted |
| ADR-0002 | Blocking questions resolved | ✅ Accepted |
| ADR-0003 | Consolidated project decisions | ✅ Accepted |

## Integration with CLAUDE.md

The root `CLAUDE.md` file serves as the agent operating manual and references this ICM layer:

```markdown
## Read on demand (not imported, to keep this file small)

- `docs/02-STATUS.md` — current project state
- `docs/03-ARCHITECTURE.md` — components, flows, contracts
- `docs/04-FOLDER-STRUCTURE.md` — repo tree, import rules
- `docs/05-IMPLEMENTATION-PLAN.md` — phases, steps, verification
- See `docs/ICM-INDEX.md` for complete catalog
```

## Document Maintenance

### Updating Status
- Update `02-STATUS.md` after completing any phase milestone
- Record new decisions in `10-OPEN-QUESTIONS.md` decision log
- Create ADR in `adr/` for any architecture changes

### Phase Transitions
- Mark phase complete in `02-STATUS.md`
- Update `05-IMPLEMENTATION-PLAN.md` with actual results
- Check off items in `11-FINAL-CHECKLIST.md`
- Review risks in `09-RISKS-AND-EDGE-CASES.md`

### Document Lifecycle
- **Planning Phase (PH0):** All docs created and reviewed
- **Implementation Phases (PH1-PH9):** Status and ADRs updated
- **Maintenance:** Update as architecture evolves

## File Locations

All planning documents live in `docs/` to keep the repository root clean:

```
project/
├── CLAUDE.md                    # Agent operating manual (root)
├── docs/
│   ├── ICM-INDEX.md            # This file
│   ├── 00-PROJECT-BRIEF.md
│   ├── 01-STACK-AND-ABSTRACT-REVIEW.md
│   ├── 02-STATUS.md
│   ├── 02-REQUIREMENTS.md
│   ├── 03-ARCHITECTURE.md
│   ├── 04-FOLDER-STRUCTURE.md
│   ├── 05-IMPLEMENTATION-PLAN.md
│   ├── 06-DEPENDENCIES-AND-COMMANDS.md
│   ├── 07-TESTING-AND-VALIDATION.md
│   ├── 08-ROLLBACK-AND-FAILURE-HANDLING.md
│   ├── 09-RISKS-AND-EDGE-CASES.md
│   ├── 10-OPEN-QUESTIONS.md
│   ├── 11-FINAL-CHECKLIST.md
│   ├── 12-REVIEW-LOG.md
│   └── adr/
│       ├── 0001-screen-source-and-auto-code-discovery.md
│       ├── 0002-blocking-questions-resolved.md
│       └── 0003-consolidated-project-decisions.md
```

## Related Resources

- **Project Repository:** Current working directory
- **Skills Available:** `icm-architect`, `icm-mvc-structure`, `graphify-windows`
- **MCP Servers:** GitHub, Obsidian, Reticle (browser testing)
- **Development Tools:** Docker, FastAPI, React+Vite, PostgreSQL

## Usage Guidelines

### For Claude/AI Agents
1. Always check `02-STATUS.md` first to understand current phase
2. Read relevant architecture sections before implementing
3. Follow dependency rules in `04-FOLDER-STRUCTURE.md`
4. Never modify files outside current phase scope without approval
5. Create ADRs for any architectural decisions

### For Human Developers
1. Use this index to navigate documentation
2. Check status before starting work
3. Follow phase-gate workflow in implementation plan
4. Document all decisions in ADRs
5. Update status document after milestones

## Document Conventions

- **✅ Complete:** Document is finished and stable
- **🔄 Active:** Document is actively maintained/updated
- **⏭️ Future:** Document will be created in future phase
- **[Qn]:** Content depends on answered question
- **[PHn]:** Content created/modified in phase n
- **P0/P1/P2:** Priority levels (0=critical, 1=important, 2=nice-to-have)

---

**Last Updated:** 2026-10-04  
**Maintained By:** Project documentation system  
**Review Cycle:** Updated with each phase transition