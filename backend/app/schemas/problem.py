"""
Problem and TestCase schemas for the coding problem bank.
"""

from typing import List, Optional
from pydantic import BaseModel, Field


class TestCase(BaseModel):
    """A test case for a coding challenge."""
    id: str = Field(..., description="Unique test case ID (e.g., tc_1)")
    stdin: str = Field(default="", description="Input fed into standard input")
    expected_output: str = Field(..., description="Expected standard output")
    is_hidden: bool = Field(default=False, description="Whether this is a private verification test")
    description: Optional[str] = Field(default=None, description="Short description of what is tested")


class ProblemSummary(BaseModel):
    """Lightweight summary of a coding problem for list views."""
    id: str
    title: str
    difficulty: str  # "easy", "medium", "hard"
    category: str
    tags: List[str] = Field(default_factory=list)
    public_test_count: int
    total_test_count: int


class Problem(BaseModel):
    """Complete definition of a coding problem."""
    id: str
    title: str
    difficulty: str  # "easy", "medium", "hard"
    category: str
    description: str
    starter_code: str
    timeout_seconds: float = 5.0
    tags: List[str] = Field(default_factory=list)
    test_cases: List[TestCase] = Field(default_factory=list)

    def to_summary(self) -> ProblemSummary:
        """Convert to lightweight summary."""
        public_count = sum(1 for tc in self.test_cases if not tc.is_hidden)
        return ProblemSummary(
            id=self.id,
            title=self.title,
            difficulty=self.difficulty,
            category=self.category,
            tags=self.tags,
            public_test_count=public_count,
            total_test_count=len(self.test_cases),
        )

    def sanitized_for_client(self) -> "Problem":
        """
        Return a copy of the problem where hidden test cases do not reveal expected outputs or inputs.
        """
        client_tests = []
        for tc in self.test_cases:
            if tc.is_hidden:
                client_tests.append(
                    TestCase(
                        id=tc.id,
                        stdin="[Hidden Test Case]",
                        expected_output="[Hidden Expected Output]",
                        is_hidden=True,
                        description=tc.description or "Hidden verification case",
                    )
                )
            else:
                client_tests.append(tc)

        return Problem(
            id=self.id,
            title=self.title,
            difficulty=self.difficulty,
            category=self.category,
            description=self.description,
            starter_code=self.starter_code,
            timeout_seconds=self.timeout_seconds,
            tags=self.tags,
            test_cases=client_tests,
        )
