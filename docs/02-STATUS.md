# Project Status

**Current status:** Feature-complete local MVP across PH0–PH9.  
**Last updated:** 2026-10-07  
**Branch:** `main`

## Phase completion

| Phase | Scope | Status |
|---|---|---|
| PH0 | Toolchain, Docker/Compose, configuration, CI | ✅ |
| PH1 | Monaco + WebSocket live analysis lifecycle | ✅ |
| PH2 | AST + Tree-sitter + Ruff + taxonomy + aggregation | ✅ |
| PH3 | Dedicated sandbox + Python/JS/C++/Java execution + tests | ✅ |
| PH4 | Progressive mentor, local/hosted OpenAI-compatible LLM, fallback and H4 gating | ✅ |
| PH5 | Sessions, analyses, hints, retention and privacy-by-default persistence | ✅ |
| PH6 | Analytics and transparent hint adaptation | ✅ |
| PH7 | Browser screen capture, OCR, confidence gating, tracking and manual region | ✅ |
| PH8 | JavaScript, C++, Java and C execution paths; Python remains richest static-analysis path | ✅ |
| PH9 | Hardening, Docker secret exclusion, CI/browser/sandbox tests, docs and desktop overlay | ✅ |

## Important implementation notes

- The live editor path uses a single canonical diagnostic protocol.
- Real-time analysis is asynchronous and sequence-safe.
- Persistence is decoupled from WebSocket response latency.
- Code text is not stored by default; only hashes/findings/metrics are persisted.
- The sandbox runner is the only component with the Docker socket.
- The in-app floating mentor is always available when `FLOATING_MENTOR_ENABLED=true`.
- The desktop overlay is an optional companion under `desktop_overlay/`.
- Screen source is opt-in and defaults to false.
- Low-confidence screen regions yield no diagnostics.
- H1–H3 avoid complete solutions; H4 requires explicit confirmation.
- If the LLM is unavailable, deterministic template hints keep mentoring functional.

## Verification status

Automated regression tests have been added for:
- diagnostic normalization
- stale WebSocket results
- screen diagnostic normalization
- sandbox policy
- Docker sandbox network/filesystem isolation
- browser workspace smoke loading

This environment cannot honestly certify a fresh Docker/Node execution of the final commit, so CI remains the authoritative clean-checkout verification.

## Remaining production hardening

The sandbox runner has Docker socket access by design for this local MVP. For a public multi-tenant deployment, move execution into a stronger isolation boundary such as dedicated worker VMs/rootless isolated runtimes, and add authenticated user identity instead of bearer session tokens alone.
