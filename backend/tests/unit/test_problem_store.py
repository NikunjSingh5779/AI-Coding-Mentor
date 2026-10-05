"""
Unit tests for the FileProblemStore and problem sanitization.
"""

from app.problems.store import FileProblemStore


def test_problem_store_loads_seeds():
    """Verify that all seed problems load correctly."""
    store = FileProblemStore()
    problems = store.list_problems()
    assert len(problems) >= 5

    two_sum = store.get_problem("two-sum")
    assert two_sum is not None
    assert two_sum.title == "Two Sum"
    assert len(two_sum.test_cases) >= 2


def test_problem_sanitization_hides_private_tests():
    """Verify that hidden test cases do not reveal expected outputs in sanitized models."""
    store = FileProblemStore()
    problem = store.get_problem("two-sum")
    assert problem is not None

    sanitized = problem.sanitized_for_client()
    for tc in sanitized.test_cases:
        if tc.is_hidden:
            assert tc.expected_output == "[Hidden Expected Output]"
            assert tc.stdin == "[Hidden Test Case]"
        else:
            assert tc.expected_output != "[Hidden Expected Output]"
