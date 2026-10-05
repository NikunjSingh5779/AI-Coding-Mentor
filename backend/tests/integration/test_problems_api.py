"""
Integration tests for problem and execution API endpoints.
"""

import pytest
from httpx import ASGITransport, AsyncClient
from app.main import app


@pytest.mark.asyncio
async def test_list_problems_endpoint():
    """Verify GET /api/v1/problems returns list of problem summaries."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/problems")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 5
        assert "title" in data[0]
        assert "difficulty" in data[0]


@pytest.mark.asyncio
async def test_get_problem_details_endpoint():
    """Verify GET /api/v1/problems/{problem_id} returns sanitized problem."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/problems/two-sum")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "two-sum"
        assert "starter_code" in data
        assert len(data["test_cases"]) > 0

        # Verify hidden test sanitization
        for tc in data["test_cases"]:
            if tc["is_hidden"]:
                assert tc["expected_output"] == "[Hidden Expected Output]"


@pytest.mark.asyncio
async def test_get_nonexistent_problem():
    """Verify GET /api/v1/problems/unknown returns 404."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/problems/nonexistent-problem-id")
        assert response.status_code == 404
