"""
Resource and limit tests for the sandbox runner.
Verifies watchdog timeout on infinite loops, memory bomb termination, output capping, and stdin handling.
"""

import pytest


@pytest.mark.asyncio
async def test_infinite_loop_timeout(async_client):
    """Verify that an infinite loop is killed by the watchdog timeout."""
    payload = {
        "job_id": "test_timeout",
        "language": "python",
        "files": {
            "main.py": (
                "import time\n"
                "while True:\n"
                "    time.sleep(0.1)\n"
            )
        },
        "limits": {
            "timeout_seconds": 2.0
        }
    }

    response = await async_client.post("/jobs", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "timeout"
    assert "timed out" in data["stderr"].lower()


@pytest.mark.asyncio
async def test_memory_bomb_killed(async_client):
    """Verify that excessive memory allocation triggers OOM kill or memory limit status."""
    payload = {
        "job_id": "test_oom",
        "language": "python",
        "files": {
            "main.py": (
                "# Try to allocate 500 MB (limit is 128 MB)\n"
                "x = bytearray(500 * 1024 * 1024)\n"
                "print('ALLOCATED')\n"
            )
        },
        "limits": {
            "memory_mb": 128
        }
    }

    response = await async_client.post("/jobs", json=payload)
    assert response.status_code == 200
    data = response.json()
    # Either process was killed by kernel OOM (exit code 137 or status memory_limit) or Python MemoryError
    assert data["status"] in ("memory_limit", "error")
    assert "ALLOCATED" not in data["stdout"]


@pytest.mark.asyncio
async def test_output_capping(async_client):
    """Verify that excessive output is truncated at the 64 KB cap (P-08)."""
    payload = {
        "job_id": "test_output_cap",
        "language": "python",
        "files": {
            "main.py": (
                "# Generate 120 KB of text\n"
                "print('A' * 120_000)\n"
            )
        }
    }

    response = await async_client.post("/jobs", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["truncated"] is True
    assert len(data["stdout"]) <= 65536 + 200  # 64KB plus marker


@pytest.mark.asyncio
async def test_stdin_data_piping(async_client):
    """Verify that standard input is correctly piped into the program."""
    payload = {
        "job_id": "test_stdin",
        "language": "python",
        "files": {
            "main.py": (
                "import sys\n"
                "name = input().strip()\n"
                "print(f'Hello, {name}!')\n"
            )
        },
        "stdin": "Nikunj\n"
    }

    response = await async_client.post("/jobs", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "Hello, Nikunj!" in data["stdout"]


@pytest.mark.asyncio
async def test_mode_test_cases(async_client):
    """Verify test-case execution mode with expected vs actual output comparison."""
    payload = {
        "job_id": "test_cases",
        "language": "python",
        "files": {
            "main.py": (
                "num = int(input().strip())\n"
                "print(num * 2)\n"
            )
        },
        "mode": "test",
        "tests": [
            {
                "id": "tc1",
                "stdin": "5\n",
                "expected_output": "10\n",
                "is_hidden": False,
            },
            {
                "id": "tc2",
                "stdin": "7\n",
                "expected_output": "14\n",
                "is_hidden": True,
            },
            {
                "id": "tc3",
                "stdin": "3\n",
                "expected_output": "99\n",  # Intentional fail
                "is_hidden": False,
            },
        ]
    }

    response = await async_client.post("/jobs", json=payload)
    assert response.status_code == 200
    data = response.json()
    test_results = data["test_results"]
    assert len(test_results) == 3
    assert test_results[0]["passed"] is True
    assert test_results[1]["passed"] is True
    assert test_results[2]["passed"] is False
