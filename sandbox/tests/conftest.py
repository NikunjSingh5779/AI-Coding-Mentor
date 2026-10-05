"""
Pytest configuration for sandbox tests.
"""

import sys
from pathlib import Path
import pytest
from httpx import ASGITransport, AsyncClient

# Add runner directory to sys.path
runner_dir = Path(__file__).parent.parent / "runner"
if str(runner_dir) not in sys.path:
    sys.path.insert(0, str(runner_dir))

from app import app


@pytest.fixture
async def async_client():
    """Create async test client for sandbox runner."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client
