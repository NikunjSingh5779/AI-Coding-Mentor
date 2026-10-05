# ADR-0004: Fast Static Analysis Baseline and Taxonomy Mapping

**Date:** 2026-10-05  
**Status:** Accepted  
**Phase:** PH2 — Fast Static Analysis

## Context

Phase 2 replaces placeholder diagnostics with a production-ready static analysis pipeline that runs error-tolerant parsing (Tree-sitter), precise syntax checks (standard library `ast.parse` in a safe worker), and comprehensive linting (`ruff`) in parallel, mapping all findings to a language-agnostic taxonomy.

## Decision

1. **Taxonomy & Category Mapping**: Standardized 23 categories across 8 groups (`syntax`, `name`, `type`, `runtime`, `logic`, `quality`, `performance`, `environment`) defined in `backend/app/analysis/taxonomy.py`.
2. **Aggregator & Fingerprinting**: Implemented `backend/app/analysis/aggregator.py` with normalized line content hashing for issue stability across edits.
3. **Multi-Analyzer Pipeline**: Concurrently orchestrates AST parser, Tree-sitter error recovery, and Ruff linter with a 2.0s worker timeout without blocking the event loop.
4. **Evaluation Harness**: Built standard evaluation suite in `eval/` with labelled test cases (`eval/datasets/code_bugs/`), accuracy/recall measurement (`eval/harness/run_eval.py`), and latency benchmarking (`eval/harness/bench_latency.py`).

## Measured Baseline

- **Precision:** 1.0 (100%)
- **Recall:** 1.0 (100%)
- **Latency P50:** 29.3 ms
- **Latency P95:** 31.0 ms (Target P-02 < 1000ms, typical < 50ms)
- **Concurrency & Safety:** All analyzers run asynchronously in threadpools and compile text without executing untrusted code.

## Consequences

- Static analysis latency is well within real-time keystroke budgets (<50ms).
- Diagnostics are cleanly categorized for downstream progressive hint generation (Phase 4).
- Ready for Phase 3 (Sandbox and Execution).
