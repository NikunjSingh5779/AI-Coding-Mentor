"""
Fast Static Analysis Pipeline Orchestrator.
Runs AST syntax checking, Tree-sitter error extraction, and Ruff linter concurrently.
"""

import asyncio
import time
from typing import List, Dict, Any, Tuple
from app.schemas.diagnostic import Diagnostic
from app.analysis.aggregator import DiagnosticsAggregator
from app.analysis.python_ast import analyze_python_ast
from app.analysis.treesitter.errors import extract_treesitter_diagnostics
from app.analysis.linters.ruff_python import RuffPythonLinter


class AnalysisPipeline:
    """Fast-path static analysis pipeline for code snapshots."""

    def __init__(self):
        self.aggregator = DiagnosticsAggregator()
        self.ruff_linter = RuffPythonLinter()

    async def analyze(
        self,
        code: str,
        language: str = "python",
        seq: int = 0
    ) -> Tuple[List[Diagnostic], Dict[str, float]]:
        """
        Run analyzers concurrently in a threadpool to not block the event loop.
        Returns aggregated diagnostics and stage timings in milliseconds.
        """
        if not code:
            return [], {}

        stage_timings: Dict[str, float] = {}
        all_diagnostics: List[Diagnostic] = []
        loop = asyncio.get_running_loop()

        # Helper to run synchronous analyzer and measure its duration
        def _run_ast():
            t0 = time.perf_counter()
            diags = analyze_python_ast(code, seq=seq)
            elapsed = (time.perf_counter() - t0) * 1000
            return "ast", diags, elapsed

        def _run_treesitter():
            t0 = time.perf_counter()
            diags = extract_treesitter_diagnostics(code, language=language, seq=seq)
            elapsed = (time.perf_counter() - t0) * 1000
            return "treesitter", diags, elapsed

        def _run_ruff():
            t0 = time.perf_counter()
            diags = self.ruff_linter.lint(code, filename="snippet.py", seq=seq)
            elapsed = (time.perf_counter() - t0) * 1000
            return "ruff", diags, elapsed

        # Execute concurrent tasks in default thread pool
        t_total_start = time.perf_counter()

        tasks = [
            loop.run_in_executor(None, _run_ast),
            loop.run_in_executor(None, _run_treesitter),
            loop.run_in_executor(None, _run_ruff),
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        for res in results:
            if isinstance(res, Exception):
                continue
            name, diags, duration_ms = res
            stage_timings[name] = round(duration_ms, 2)
            all_diagnostics.extend(diags)

        # Aggregate and deduplicate
        t_agg_start = time.perf_counter()
        code_lines = code.splitlines()
        aggregated = self.aggregator.aggregate(all_diagnostics, code_lines=code_lines)
        stage_timings["aggregator"] = round((time.perf_counter() - t_agg_start) * 1000, 2)
        stage_timings["total"] = round((time.perf_counter() - t_total_start) * 1000, 2)

        return aggregated, stage_timings
