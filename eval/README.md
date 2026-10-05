# Evaluation Suite for AI Coding Mentor

This evaluation suite provides benchmarks and quality metrics for:
- Fast static analysis precision and recall (Phase 2)
- Fast-path latency and throughput benchmarks (Phase 2)
- Progressive hint quality and guardrail compliance (Phase 4)
- Screen OCR and code region detection accuracy (Phase 7)

## Running Evaluations

### 1. Run Analysis Evaluation Suite
```bash
python -m harness.run_eval --suite analysis
```

### 2. Run Latency Benchmark
```bash
python -m harness.bench_latency --runs 20
```

### 3. Generate Evaluation Report
Reports are written to `eval/reports/` with timestamped JSON and markdown summaries.
