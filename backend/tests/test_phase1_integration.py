"""Integration tests for the live Fast Static Analysis pipeline."""

import time

import pytest

from app.analysis.pipeline import AnalysisPipeline
from app.schemas.diagnostic import Origin, Severity


@pytest.mark.asyncio
async def test_pipeline_detects_python_syntax_errors() -> None:
    pipeline = AnalysisPipeline()
    code = "def invalid_syntax(\n    print('missing paren')"

    diagnostics, timings = await pipeline.analyze(code, seq=7)

    assert diagnostics
    assert timings["total"] >= 0
    assert any(
        diagnostic.origin in {Origin.PARSER, Origin.TREESITTER}
        and diagnostic.severity == Severity.ERROR
        for diagnostic in diagnostics
    )
    assert all(diagnostic.seq == 7 for diagnostic in diagnostics)


@pytest.mark.asyncio
async def test_pipeline_detects_undefined_name() -> None:
    pipeline = AnalysisPipeline()
    code = "def test_func():\n    return undefined_var\n"

    diagnostics, _ = await pipeline.analyze(code, seq=1)

    undefined = [
        diagnostic
        for diagnostic in diagnostics
        if diagnostic.rule == "F821"
    ]
    assert undefined
    assert undefined[0].category == "NAME_UNDEFINED"


@pytest.mark.asyncio
async def test_pipeline_detects_unused_import() -> None:
    pipeline = AnalysisPipeline()
    code = "import os\n\nprint('hello')\n"

    diagnostics, _ = await pipeline.analyze(code)

    unused = [
        diagnostic
        for diagnostic in diagnostics
        if diagnostic.rule == "F401"
    ]
    assert unused
    assert unused[0].category == "QUALITY_UNUSED"


@pytest.mark.asyncio
async def test_pipeline_returns_no_errors_for_valid_code() -> None:
    pipeline = AnalysisPipeline()
    code = '''
def calculate_average(numbers: list[float]) -> float:
    if not numbers:
        return 0.0
    return sum(numbers) / len(numbers)

data = [1.0, 2.0, 3.0]
print(calculate_average(data))
'''

    diagnostics, _ = await pipeline.analyze(code)

    errors = [
        diagnostic
        for diagnostic in diagnostics
        if diagnostic.severity == Severity.ERROR
    ]
    assert errors == []


@pytest.mark.asyncio
async def test_pipeline_reports_stage_timings() -> None:
    pipeline = AnalysisPipeline()
    started = time.perf_counter()

    diagnostics, timings = await pipeline.analyze(
        "def add(a, b):\n    return a + b\n"
    )

    elapsed_ms = (time.perf_counter() - started) * 1000
    assert isinstance(diagnostics, list)
    assert "total" in timings
    assert timings["total"] <= elapsed_ms + 20
    assert timings["total"] < 500


@pytest.mark.asyncio
async def test_pipeline_preserves_sequence_and_handles_empty_input() -> None:
    pipeline = AnalysisPipeline()

    diagnostics, timings = await pipeline.analyze("", seq=99)
    assert diagnostics == []
    assert timings == {}

    diagnostics, _ = await pipeline.analyze(
        "x = 1\n",
        seq=123,
    )
    assert all(diagnostic.seq == 123 for diagnostic in diagnostics)
