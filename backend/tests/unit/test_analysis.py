"""
Unit tests for Fast Static Analysis pipeline components (Phase 2).
"""

import pytest
from app.schemas.diagnostic import Severity, Origin
from app.analysis.taxonomy import Category, map_rule_to_category
from app.analysis.aggregator import DiagnosticsAggregator, compute_fingerprint
from app.analysis.python_ast import analyze_python_ast
from app.analysis.treesitter.errors import extract_treesitter_diagnostics
from app.analysis.linters.ruff_python import RuffPythonLinter
from app.analysis.pipeline import AnalysisPipeline


def test_taxonomy_mapping():
    assert map_rule_to_category("F821") == Category.NAME_UNDEFINED
    assert map_rule_to_category("F401") == Category.QUALITY_UNUSED
    assert map_rule_to_category("E111") == Category.SYNTAX_INDENTATION
    assert map_rule_to_category("unknown_rule") == Category.SYNTAX_UNEXPECTED_TOKEN


def test_compute_fingerprint_stability():
    fp1 = compute_fingerprint("SYNTAX_MISSING_TOKEN", "E999", "func", "def foo(x):")
    fp2 = compute_fingerprint("SYNTAX_MISSING_TOKEN", "E999", "func", "  def   foo(x):  ")
    assert fp1 == fp2
    assert len(fp1) == 16


def test_python_ast_clean():
    code = "def add(a, b):\n    return a + b\n"
    diags = analyze_python_ast(code)
    assert len(diags) == 0


def test_python_ast_syntax_error():
    code = "def foo(\n    return 42\n"
    diags = analyze_python_ast(code)
    assert len(diags) >= 1
    assert diags[0].origin == Origin.PARSER
    assert diags[0].severity == Severity.ERROR
    assert diags[0].range.start.line == 1


def test_treesitter_syntax_error():
    code = "def bar(x\n    pass\n"
    diags = extract_treesitter_diagnostics(code, "python")
    assert len(diags) >= 1
    assert diags[0].origin == Origin.TREESITTER
    assert diags[0].severity == Severity.ERROR


def test_ruff_linter_undefined_name():
    linter = RuffPythonLinter()
    if not linter.is_available():
        pytest.skip("Ruff not available")

    code = "def run():\n    print(undefined_variable)\n"
    diags = linter.lint(code)
    f821_diags = [d for d in diags if d.rule == "F821"]
    assert len(f821_diags) == 1
    assert f821_diags[0].category == Category.NAME_UNDEFINED.value


@pytest.mark.asyncio
async def test_analysis_pipeline_e2e():
    pipeline = AnalysisPipeline()
    code = "import os\n\ndef broken():\n    return non_existent\n"
    diags, timings = await pipeline.analyze(code)

    assert "total" in timings
    assert timings["total"] < 500  # Well within latency limits

    categories = {d.category for d in diags}
    assert Category.NAME_UNDEFINED.value in categories or Category.QUALITY_UNUSED.value in categories
