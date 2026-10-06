from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.problems.problem_bank import list_all_problems, get_problem

router = APIRouter(prefix="/problems", tags=["problems"])


@router.get("")
async def list_problems() -> list[dict]:
    return [
        {
            "id": problem["id"],
            "title": problem["title"],
            "description": problem["description"],
            "difficulty": problem["difficulty"],
            "category": problem["category"],
            "starter_code": problem.get("starter_code", ""),
        }
        for problem in list_all_problems()
    ]


@router.get("/{problem_id}")
async def read_problem(problem_id: str) -> dict:
    problem = get_problem(problem_id)
    if problem is None:
        raise HTTPException(404, "Problem not found")
    return {
        "id": problem["id"],
        "title": problem["title"],
        "description": problem["description"],
        "difficulty": problem["difficulty"],
        "category": problem["category"],
        "starter_code": problem.get("starter_code", ""),
        "test_cases": problem.get("test_cases", []),
    }
