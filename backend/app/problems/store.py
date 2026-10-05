"""
Problem store interface and file-backed implementation for the problem bank.
"""

import json
import logging
from abc import ABC, abstractmethod
from functools import lru_cache
from pathlib import Path
from typing import Dict, List, Optional

from app.schemas.problem import Problem, ProblemSummary

logger = logging.getLogger("app.problems.store")


class ProblemStore(ABC):
    """Abstract interface for problem persistence and retrieval."""

    @abstractmethod
    def list_problems(self) -> List[ProblemSummary]:
        """List all available problems as lightweight summaries."""
        pass

    @abstractmethod
    def get_problem(self, problem_id: str) -> Optional[Problem]:
        """Retrieve full problem definition by ID."""
        pass


class FileProblemStore(ProblemStore):
    """File-backed problem store that loads JSON seed definitions from disk."""

    def __init__(self, seed_dir: Optional[Path] = None):
        if seed_dir is None:
            seed_dir = Path(__file__).parent / "seed"
        self.seed_dir = seed_dir
        self._cache: Dict[str, Problem] = {}
        self._load_problems()

    def _load_problems(self):
        """Scan seed directory and parse all JSON problem files."""
        self._cache.clear()
        if not self.seed_dir.exists():
            logger.warning(f"Seed problems directory '{self.seed_dir}' does not exist.")
            return

        for path in self.seed_dir.glob("*.json"):
            try:
                content = path.read_text(encoding="utf-8")
                data = json.loads(content)
                problem = Problem(**data)
                self._cache[problem.id] = problem
            except Exception as e:
                logger.error(f"Failed to load problem from {path.name}: {e}")

        logger.info(f"Loaded {len(self._cache)} seed problems from {self.seed_dir}")

    def list_problems(self) -> List[ProblemSummary]:
        """List all problems sorted by difficulty and title."""
        diff_order = {"easy": 1, "medium": 2, "hard": 3}
        summaries = [p.to_summary() for p in self._cache.values()]
        summaries.sort(key=lambda s: (diff_order.get(s.difficulty, 9), s.title))
        return summaries

    def get_problem(self, problem_id: str) -> Optional[Problem]:
        """Get full problem definition by ID."""
        return self._cache.get(problem_id)


@lru_cache
def get_problem_store() -> ProblemStore:
    """Singleton provider for problem store."""
    return FileProblemStore()
