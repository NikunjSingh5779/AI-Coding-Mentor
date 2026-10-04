# 00 — Project Brief

**AI Real-Time Coding Screener / AI Coding Mentor**

## Goal
A web application that watches learner code as it's written, finds syntax, runtime, logic and quality problems with real tools (parsers, linters, sandboxed execution, test cases), and uses an LLM to turn verified findings into progressive hints. Never gives the full solution unless explicitly requested at the last hint level.

## Scope
- **Input Sources:** Monaco editor (primary) + screen capture with OCR (secondary)
- **Languages:** Python (MVP), extensible to C++ and Java
- **Problem Detection:** Syntax, runtime, logic (via test cases), and quality issues
- **Mentor System:** Progressive 4-level hint ladder (H1-H4) with guardrails
- **Analytics:** Learner progress tracking and mistake pattern analysis
- **Deployment:** Single-user local development environment

## Constraints
- **Safety First:** Learner code runs only in hardened sandbox
- **Privacy:** No raw screen frames stored, secrets redacted before LLM calls
- **Performance:** <1s from keystroke to diagnostic markers
- **Reliability:** Degrades gracefully when components fail
- **Security:** No execution in API process, origin-checked WebSockets

## Architecture Decisions
- **Backend:** FastAPI + PostgreSQL + async event bus
- **Frontend:** React + Vite + Monaco Editor + WebSocket client
- **Sandbox:** Docker containers with hardened policies
- **LLM:** Switchable (local LM Studio + hosted APIs)
- **Real-time:** WebSocket with sequence numbering and coalescing

## Success Criteria
1. Detects Python syntax/runtime errors within 1 second
2. Provides progressive hints without revealing solutions
3. Tracks learner progress over time
4. Runs securely in local development environment
5. Extensible architecture for additional languages

## Current Status
**Phase:** 0 - Core Infrastructure Setup  
**Timeline:** 2-week prototype  
**Blocking Questions:** Resolved (see ADR-0002)

## Key Documents
- Architecture: `03-ARCHITECTURE.md`
- Implementation: `05-IMPLEMENTATION-PLAN.md` 
- Folder Structure: `04-FOLDER-STRUCTURE.md`
- Status Tracking: `02-STATUS.md`