# 09 — Risks and Edge Cases

Likelihood and impact are my estimates (High, Medium, Low), not measurements; revisit them at every phase exit. Each risk names the requirements and phases that address it.

## 1. Risk register

| ID | Risk | Likelihood | Impact | Mitigation | Requirements | Phases |
|---|---|---|---|---|---|---|
| R-01 | Untrusted code execution: sandbox escape, resource exhaustion, host or network access | Medium | High | Separate runner with a hardened per-job policy; isolation tests in CI; no Docker socket in the API; stronger isolation if hosted; kill switch | FR-06, NFR-03 | PH3, PH9 |
| R-02 | OCR misreads produce false errors and destroy learner trust | High (screen mode) | High | Confidence gate; engine chosen by bake-off; indentation reconstruction; notices instead of guesses; editor source as the reliable path | FR-19, FR-20 | PH7 |
| R-03 | Real-time latency target missed: heavy local model with limited VRAM, several analyzers, the LLM competing with everything else on one laptop | Medium | Medium | Fast path separated from slow work; stage timings; benchmark; templates when the LLM is slow; model bake-off includes latency | NFR-01, NFR-02 | PH2, PH4, PH9 |
| R-04 | LLM hallucination: wrong cause, wrong line, invented identifiers | High | Medium | LLM receives tool-verified diagnostics, not raw guesses; grounding guardrails; templates; evals with a human rubric | FR-10, FR-12 | PH4 |
| R-05 | Solution leakage and prompt injection (learners pushing for answers; hostile comments or OCR text) | Medium | Medium | Guardrails; data-not-instructions framing; no tools for the model; H4 only on explicit request; adversarial suite. Residual risk: leakage in prose cannot be eliminated and is measured | FR-11, FR-12 | PH4 |
| R-06 | Over-promising logic-error detection with no oracle | High | High | Tests as the oracle; `suspicion` labelling; honest documentation of the limit | FR-07 | PH3, PH4 |
| R-07 | False alarms while typing and hint fatigue erode trust | High | Medium | Settle debounce, persistence wait, cooldown, rate limit, proactivity setting; tuned on typing traces | FR-13 | PH4, PH9 |
| R-08 | Privacy of captured screens and code: other windows, secrets, hosted-LLM disclosure | Medium | High | Consent, region select, indicator, no frame persistence, redaction before LLM calls, local-LLM option, disclosure | NFR-04 | PH1, PH4, PH5, PH7 |
| R-09 | Browser screen-capture limits: permission every session, browser and OS differences, background-tab throttling, shared window closing | High | Medium | Feasibility spike on your browser and OS; editor source as the fallback; clear notices | FR-19 | PH7 |
| R-10 | Scope creep and schedule: several languages, two sources, analytics, with an unknown deadline | High | High | Phases with gates; explicit cut order; Q6; backlog with triggers | all | PH0, PH9 |
| R-11 | Tooling and dependency drift: Tree-sitter bindings, Tailwind and shadcn/ui setup, the fast-moving model landscape | Medium | Medium | Pin versions at scaffold; verify against current docs; interfaces at the seams; bake-offs instead of fixed model names | NFR-07 | PH0 |
| R-12 | Agent-driven development drift: unrelated edits, unverified claims, silent assumptions | Medium | High | `CLAUDE.md` rules; per-phase file lists; `git diff --stat` in every report; real verification output; phase gates | NFR-07 | all |
| R-13 | Evaluation data too small or biased, giving misleading quality claims | High | Medium | Report counts; clean negatives; human-reviewed labels; grow the set from real misses | FR-04, FR-05 | PH2, PH4, PH9 |
| R-14 | Sandbox environment differs from what learners expect (packages, versions, stdin), producing "errors" that are not their fault | Medium | Medium | ENV_UNSUPPORTED category; package and version policy (Q11); clear messages; stdin handling | FR-06 | PH3 |
| R-15 | Hosted-LLM cost or quota overrun | Low if local, Medium if hosted | Medium | Budgets, cache, call coalescing, templates on exhaustion | NFR-11 | PH4 |
| R-16 | Resource contention and scale on one node: OCR CPU, sandbox concurrency, GPU shared with the model, many learners if hosted | Medium if hosted | Medium | Concurrency limits, worker pools, measurement; multi-node is out of scope | NFR-01, NFR-03 | PH3, PH9 |
| R-17 | Automatic code-region discovery selects the wrong window/text block or loses the editor after movement | Medium | High | Multi-signal scoring, region confidence gate, parser validation, tracking/reacquisition, evaluation corpus with non-code distractors, manual fallback | FR-27, NFR-04, NFR-05 | PH7, PH9 |
| R-18 | Floating mentor blocks the active code area, appears detached from the issue, or keeps stale geometry after a move | Medium | Medium | Geometry-based placement, obstruction threshold P-17, drag override, stale-state invalidation, in-page fallback | FR-28, NFR-10 | PH4, PH7, PH9 |

## 2. Edge cases

Each is either handled by a named mechanism or listed as a known limitation.

### Input and sources

- Empty, whitespace-only, very large, binary, non-UTF-8, null-byte or single-very-long-line input: rejected or truncated by validation (P-10); never crashes the pipeline.
- Tabs mixed with spaces, CRLF versus LF, Unicode identifiers, zero-width characters: normalised for analysis; reported positions refer to the original text.
- Rapid typing bursts, large pastes, undo and redo: coalescing keeps only the latest snapshot.
- Two tabs on the same session: one active connection per session; the newer one takes over and the older shows a notice.
- Language selector disagrees with the code: parse failures spike; a language-mismatch notice is a possible later addition and not a v1 requirement.
- Screen mode: dark themes, ligatures, small fonts, high-DPI scaling, zoom, several monitors, notification pop-ups over the code, partly scrolled code, gutters and minimaps, wrapped long lines, split panes, a minimised or closed shared window, a sleeping screen, two code-like windows and non-code text blocks. Automatic region discovery/tracking, confidence gates and notices handle these cases; some combinations remain unreadable, and that is reported rather than guessed.
- Sharing the whole screen exposes other windows: automatic discovery narrows processing to a candidate code region, but capture permission still covers the permitted surface; region processing must be minimized, raw frames are never persisted, and manual region selection remains available as the privacy fallback.

### Analysis

- Incomplete code while typing produces transient errors: the mentor waits for settle; markers update immediately but are not escalated.
- One syntax error causes cascades: show the first, suppress dependent noise.
- Several tools report the same problem: deduplicated by range overlap and category.
- Positions differ between tools: the aggregator normalises ranges and keeps the more precise one.
- The backend interpreter's Python version differs from the learner's target (new syntax such as pattern matching): documented limitation tied to Q11; the sandbox run is authoritative.
- Style rules the learner does not need: severity filtering so style findings stay `info`.
- Tool missing or crashing: that analyzer is skipped and a notice names it.

### Execution

- Programs that read input, use randomness, time, threads or files, or sleep: stdin handling and wall limit; flaky tests are a limitation of such problems and are not seeded.
- Output differences that are not errors (trailing whitespace, floating-point formatting): trailing whitespace is normalised; problems with several valid answers would need a custom checker, which is out of scope for v1.
- Cold image start, JVM start-up, compile-time bombs, runner restart mid-job, Docker daemon down: timeouts, "busy" and "unavailable" states, circuit breaker.
- Learner imports a package that is not installed: ENV_UNSUPPORTED, not a learner error.

### Mentor

- Automatic region changes while a hint is pending: drop the hint if its region or diagnostic no longer matches the current state.
- Floating overlay has no safe position near a code region: dock it inside the mentor panel rather than covering code.


- Several issues at once: rank by severity then position, first error first; at most one proactive hint at a time.
- The learner clicks straight through the ladder to H4: allowed by design (H4 still needs a confirmation); the behaviour is recorded in analytics, not blocked.
- A hint arrives after the code changed: the engine drops it if its issue was resolved or its fingerprint is no longer present.
- Very large files or small local context windows: the prompt uses an excerpt around the diagnostic within a token budget.
- Comments or identifiers in another language, or offensive text in code: treated as data; explanations follow Q8.
- The model explains correctly but too advanced for a beginner: caught by the clarity rubric in the hints eval.

### Data and privacy

- Secrets pasted into code: redacted before any LLM call and before storage of code text.
- Delete-my-data must cover every table; dashboard figures are computed from retained data only and will change after a purge.
- A shared computer in single-user mode: records are tied to the local profile; stated in the README.
- Time zones and clock skew: store UTC; the server's timestamps are authoritative.

### Interface and platform

- Colour-only severity cues, keyboard-only use, screen-reader announcement of new hints, reduced motion: addressed in PH9 (NFR-10).
- Small screens: the workspace targets desktop-width browsers; mobile is out of scope.
- A network that blocks WebSockets, or hosted use without TLS (screen capture and secure WebSockets need it): documented requirements.
- Monaco defaults to loading from a CDN: bundled locally so offline demos work.
- Laptop sleep during a session: WebSocket drop, then resume.
- Thermal or battery throttling while a local model runs: shows up as latency; the benchmark notes the power state.
