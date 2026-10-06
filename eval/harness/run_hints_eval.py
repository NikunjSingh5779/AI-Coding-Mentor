"""Hints evaluation: guardrail pass rate and latency for template fallbacks.

Runs the mentor's deterministic fallback chain (no live LLM required) over
the labelled corpus and reports guardrail pass rate, per-category coverage
and latency. When LLM_ENABLED=true a live-LLM variant measures the full path.
"""

from __future__ import annotations

import asyncio
import json
import sys
import time
from pathlib import Path

root_dir = Path(__file__).resolve().parent.parent.parent
backend_dir = root_dir / "backend"
eval_dir = root_dir / "eval"

for p in (str(backend_dir), str(eval_dir)):
    if p not in sys.path:
        sys.path.insert(0, p)

from app.analysis.pipeline import AnalysisPipeline  # noqa: E402
from app.mentor.engine import MentorBudget, MentorEngine  # noqa: E402
from app.mentor.llm.registry import reset_llm_provider  # noqa: E402
from harness.judges import judge_hint  # noqa: E402
from harness.report import save_report  # noqa: E402


async def run_hints_evaluation() -> dict:
    dataset_dir = eval_dir / "datasets" / "code_bugs" / "python"
    cases = sorted(dataset_dir.glob("*.json"))
    if not cases:
        print("No evaluation cases found.")
        return {}

    pipeline = AnalysisPipeline()
    reset_llm_provider()

    import os

    os.environ["LLM_ENABLED"] = "false"  # template mode for the deterministic eval

    from app.config import get_settings

    get_settings.cache_clear()

    engine = MentorEngine(budget=MentorBudget(session_limit=1000, day_limit=1000))

    total = 0
    guardrail_pass = 0
    hint_generated = 0
    latencies: list[float] = []
    per_case = []

    print(f"Running hints evaluation on {len(cases)} cases (template mode)...")

    for case_file in cases:
        with open(case_file, "r", encoding="utf-8") as f:
            metadata = json.load(f)
        code_file = case_file.with_suffix(".py")
        if not code_file.exists():
            continue
        code = code_file.read_text(encoding="utf-8")

        diags, _ = await pipeline.analyze(code)
        if not diags:
            continue

        diag_dicts = [d.model_dump() for d in diags]
        engine.track_issues(seq=1, diagnostics=diags)

        t0 = time.perf_counter()
        hint, notice = await engine.generate_hint(
            issue_id=diags[0].fingerprint, level=None, code=code, diagnostics=diag_dicts
        )
        elapsed_ms = (time.perf_counter() - t0) * 1000
        latencies.append(elapsed_ms)

        total += 1
        if hint is not None:
            hint_generated += 1
            judgement = judge_hint(hint.text, hint.level)
            if judgement.passed:
                guardrail_pass += 1
            per_case.append(
                {
                    "case": case_file.stem,
                    "category": hint.category,
                    "level": hint.level,
                    "source": hint.source,
                    "guardrail_pass": judgement.passed,
                    "failures": judgement.failures,
                    "latency_ms": round(elapsed_ms, 1),
                }
            )
        else:
            per_case.append(
                {"case": case_file.stem, "hint": None, "notice": notice, "latency_ms": round(elapsed_ms, 1)}
            )

    latencies.sort()

    def pct(p: float) -> float:
        if not latencies:
            return 0.0
        idx = min(int(p / 100 * len(latencies)), len(latencies) - 1)
        return round(latencies[idx], 1)

    report = {
        "suite": "hints",
        "mode": "template",
        "total_cases": total,
        "hints_generated": hint_generated,
        "hint_coverage": round(hint_generated / total, 3) if total else 0.0,
        "guardrail_pass_rate": round(guardrail_pass / hint_generated, 3) if hint_generated else 0.0,
        "latency_ms_p50": pct(50),
        "latency_ms_p95": pct(95),
        "cases": per_case,
    }

    print(f"Hint coverage: {report['hint_coverage']:.1%}")
    print(f"Guardrail pass rate: {report['guardrail_pass_rate']:.1%}")
    print(f"Latency P50/P95: {report['latency_ms_p50']}ms / {report['latency_ms_p95']}ms")

    return report


if __name__ == "__main__":
    report = asyncio.run(run_hints_evaluation())
    if report:
        # save_report signature: (report_data, report_type)
        save_report(report, "hints_eval")
