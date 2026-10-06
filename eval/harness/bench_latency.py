"""
Latency and Throughput Benchmark for Fast Static Analysis.
Measures latency percentiles against target limits (e.g. P-02 < 1000ms, typical < 50ms).
"""

import asyncio
import sys
import time
from pathlib import Path

# Add backend and eval directories to sys.path
root_dir = Path(__file__).resolve().parent.parent.parent
backend_dir = root_dir / "backend"
eval_dir = root_dir / "eval"
for p in (str(backend_dir), str(eval_dir)):
    if p not in sys.path:
        sys.path.insert(0, p)

from app.analysis.pipeline import AnalysisPipeline
from harness.metrics import calculate_percentiles
from harness.report import save_report


TRACES = [
    "def ",
    "def calc",
    "def calculate(a, b):",
    "def calculate(a, b):\n    return a +",
    "def calculate(a, b):\n    return a + b",
    "import math\n\ndef dist(x1, y1, x2, y2):\n    return math.sqrt((x2 - x1)**2 + (y2 - y1)**2)",
    "class Greeter:\n    def __init__(self, name):\n        self.name = name\n    def greet(self):\n        return f'Hello {self.name}'",
]


async def run_latency_benchmark(num_runs: int = 20) -> dict:
    pipeline = AnalysisPipeline()
    latencies = []

    print(f"Running latency benchmark across {len(TRACES)} traces x {num_runs} iterations...")

    # Warm-up run
    for code in TRACES:
        await pipeline.analyze(code)

    for run_idx in range(num_runs):
        for code in TRACES:
            t0 = time.perf_counter()
            diags, timings = await pipeline.analyze(code)
            elapsed_ms = (time.perf_counter() - t0) * 1000
            latencies.append(elapsed_ms)

    percentiles = calculate_percentiles(latencies)
    print("\n--- Latency Benchmark Results (ms) ---")
    for k, v in percentiles.items():
        print(f"  {k.upper()}: {v} ms")

    report_data = {
        "benchmark": "fast_static_analysis_latency",
        "sample_count": len(latencies),
        "percentiles_ms": percentiles,
        "target_p95_ms": 1000.0,
        "p95_pass": percentiles["p95"] < 1000.0,
    }

    report_path = save_report(report_data, "latency_benchmark")
    print(f"\nReport saved to {report_path}")
    return report_data


def main():
    asyncio.run(run_latency_benchmark(num_runs=15))


if __name__ == "__main__":
    main()
