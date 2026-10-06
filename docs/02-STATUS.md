# 02 — Project Status

**Current Status:** Phases 0–9 Complete — release candidate  
**Last Updated:** 2026-10-06  
**Branch:** `phase/4-mentor-engine` (phase work committed and tagged `phase-4-complete` … `phase-7-complete`; PH9 hardening in the release commit)

## ✅ Phase 0 — Decisions and scaffold

- FastAPI + uv backend, React + Vite + TypeScript frontend, PostgreSQL 15 container (host port 5433)
- CI workflow, Makefile task runner, `.env.example`, ADRs for Q1–Q7

## ✅ Phase 1 — Walking skeleton

- WebSocket pipeline with session management, coalescing and heartbeat
- Monaco editor + diagnostics panel wired through Zustand

## ✅ Phase 2 — Fast static analysis

- Taxonomy (23 categories), stable-fingerprint aggregator, Tree-sitter error extraction
- Python AST syntax analysis, Ruff subprocess wrapper
- Measured **precision 1.0 / recall 1.0**; **P50 29 ms, P95 33 ms** (`bench_latency.py`)

## ✅ Phase 3 — Sandbox and execution

- Hardened container policy: non-root UID 1000, read-only rootfs, tmpfs `/work`,
  `--network none`, all capabilities dropped, PID/memory/CPU/output caps
- Runner service on 8100 behind a shared secret; 9/9 isolation tests pass
- Runtime-error → taxonomy mapping; hidden test data never serialised to the client

## ✅ Phase 4 — Mentor engine

- LLM provider abstraction (OpenAI-compatible adapter + disabled stub + registry)
- H1–H4 ladder with **no auto-escalation**; H4 needs H3 + explicit request + confirmation
- Guardrails: no fenced code or solution phrasing at H1–H3, grounding checks, secret redaction
- Deterministic trigger policy; template fallbacks for every category (works with `LLM_ENABLED=false`)
- Adversarial tests: prompt injection, leakage, grounding, output schema
- Hints eval: **guardrail pass rate 100%**

## ✅ Phase 5 — Persistence and learner record

- Alembic async migrations; **upgrade and downgrade both verified**
- `LearnerTracker`: issue lifecycle, time-to-resolve, hint counts, checkpoints
- Privacy: checkpoints redacted; `STORE_CODE_TEXT=false` stores no code at all
- Repository layer as the only query module; session history + delete-my-data

## ✅ Phase 6 — Analytics, quality, adaptation

- Complexity/nesting and performance-pattern analyzers (thresholds chosen for zero false positives)
- Rule-based adaptation: recurring-category profile and suggested starting level
- Progress API + dashboard

## ✅ Phase 7 — Screen source, discovery, tracking, OCR

- Frame validation, multi-signal region detection (text blocks + uniform panes) with a
  confidence gate, region tracking with reacquisition, manual region override
- RapidOCR behind a swappable interface; code reconstruction with gutter stripping,
  indentation recovery and OCR confidence gating
- Privacy: `FEATURE_SCREEN_SOURCE=false` is a full no-op; low-confidence paths emit
  **no** diagnostics; frames never persisted, only hashes logged; consent required
- Measured: **region precision/recall 1.0, mean IoU 0.996; OCR line accuracy 0.99, CER 9.2%**

## ✅ Phase 8 — Additional languages (out of scope, documented)

Q2 resolved to **Python only**, so every gated PH8 deliverable is a no-op.
See `docs/adr/0007-phase-8-additional-languages-out-of-scope.md`.

## ✅ Phase 9 — Hardening, evaluation, release

- Latency benchmark re-run and recorded; mentor latency measured (template path < 1 ms)
- Security review: Origin allowlist, WS message-size limit, hint rate limiting,
  dependency audit (`pip-audit`: clean), secret scan — **which found and fixed a real
  issue: `.env` was tracked in git and is now untracked**
- Accessibility: ARIA labels on mentor/capture controls, keyboard-reachable buttons
- `backend/Dockerfile`, `frontend/Dockerfile`, `frontend/nginx.conf` for deployment
- Final `README.md`, demo script, updated checklist

## 📊 Verified metrics (2026-10-06)

| Metric | Value |
|---|---|
| Backend tests | 111 passing |
| Analysis precision / recall | 1.0 / 1.0 |
| Analysis latency | P50 29.2 ms · P95 32.7 ms |
| Hint guardrail pass rate | 100% |
| Region detection | P 1.0 · R 1.0 · IoU 0.996 |
| OCR reconstruction | line accuracy 0.99 · CER 9.2% |
| Dependency audit | clean |

**Known limitations:** screen metrics use a synthetic dataset built with a real
monospace font (real learner screenshots require consent); OCR uses RapidOCR
because no Tesseract binary is installed here; hidden-test redaction is covered by
unit tests rather than a live sandbox run in this environment.
