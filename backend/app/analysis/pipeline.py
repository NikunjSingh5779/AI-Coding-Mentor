"""Fast static-analysis pipeline."""

from __future__ import annotations

import asyncio
import time
from typing import Any

from app.analysis.aggregator import DiagnosticsAggregator
from app.analysis.linters.ruff_python import RuffPythonLinter
from app.analysis.python_ast import analyze_python_ast
from app.analysis.treesitter.errors import extract_treesitter_diagnostics
from app.config import get_settings


class AnalysisPipeline:
    def __init__(self) -> None:
        self.aggregator = DiagnosticsAggregator()
        self.ruff_linter = RuffPythonLinter()

    async def analyze(
        self, code: str, language: str = "python", seq: int = 0
    ) -> tuple[list, dict[str, float]]:
        if not code:
            return [], {}

        settings = get_settings()
        enabled = {
            item.strip().lower()
            for item in (settings.enabled_analyzers if hasattr(settings, "enabled_analyzers") else {"python_ast","treesitter","ruff"})
        }

        if language.lower() != "python":
            return [], {"total": 0.0}

        loop = asyncio.get_running_loop()
        tasks: list[asyncio.Future[Any]] = []
        names: list[str] = []

        if "python_ast" in enabled or "ast" in enabled:
            names.append("python_ast")
            tasks.append(loop.run_in_executor(None, lambda: self._timed("python_ast", analyze_python_ast, code, seq)))
        if "treesitter" in enabled:
            names.append("treesitter")
            tasks.append(loop.run_in_executor(None, lambda: self._timed("treesitter", extract_treesitter_diagnostics, code, language, seq)))
        if "ruff" in enabled:
            names.append("ruff")
            tasks.append(loop.run_in_executor(None, lambda: self._timed("ruff", self.ruff_linter.lint, code, "snippet.py", seq)))

        started = time.perf_counter()
        results = await asyncio.gather(*tasks, return_exceptions=True)
        total_ms = (time.perf_counter() - started) * 1000

        diagnostics = []
        timings: dict[str, float] = {}
        for name, result in zip(names, results, strict=False):
            if isinstance(result, Exception):
                timings[name] = 0.0
                continue
            diags, duration = result
            diagnostics.extend(diags)
            timings[name] = round(duration, 2)

        aggregate_started = time.perf_counter()
        aggregated = self.aggregator.aggregate(diagnostics, code_lines=code.splitlines())
        timings["aggregator"] = round((time.perf_counter() - aggregate_started) * 1000, 2)
        timings["total"] = round(total_ms + timings["aggregator"], 2)
        return aggregated, timings

    @staticmethod
    def _timed(name: str, func, *args):
        started = time.perf_counter()
        result = func(*args)
        return result, (time.perf_counter() - started) * 1000
