"""
Security and isolation tests for the sandbox runner.
Verifies non-root execution, network denial, read-only rootfs, and lack of host access.
"""

import pytest


@pytest.mark.asyncio
async def test_non_root_execution(async_client):
    """Verify that learner code executes as a non-root user (UID 1000)."""
    payload = {
        "job_id": "test_uid",
        "language": "python",
        "files": {
            "main.py": (
                "import os\n"
                "uid = os.getuid()\n"
                "gid = os.getgid()\n"
                "print(f'UID:{uid},GID:{gid}')\n"
            )
        },
    }

    response = await async_client.post("/jobs", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "UID:1000,GID:1000" in data["stdout"]


@pytest.mark.asyncio
async def test_network_access_blocked(async_client):
    """Verify that outbound network access is blocked (--network none)."""
    payload = {
        "job_id": "test_network",
        "language": "python",
        "files": {
            "main.py": (
                "import socket\n"
                "try:\n"
                "    s = socket.create_connection(('1.1.1.1', 80), timeout=1.0)\n"
                "    print('CONNECTED')\n"
                "except Exception as e:\n"
                "    print(f'NETWORK_BLOCKED:{type(e).__name__}')\n"
            )
        },
    }

    response = await async_client.post("/jobs", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "NETWORK_BLOCKED" in data["stdout"]
    assert "CONNECTED" not in data["stdout"]


@pytest.mark.asyncio
async def test_read_only_root_filesystem(async_client):
    """Verify that root filesystem is read-only and writes outside /work fail."""
    payload = {
        "job_id": "test_ro_fs",
        "language": "python",
        "files": {
            "main.py": (
                "try:\n"
                "    with open('/etc/evil.txt', 'w') as f:\n"
                "        f.write('fail')\n"
                "    print('WRITE_SUCCEEDED')\n"
                "except OSError as e:\n"
                "    print(f'WRITE_BLOCKED:{type(e).__name__}')\n"
            )
        },
    }

    response = await async_client.post("/jobs", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "WRITE_BLOCKED" in data["stdout"]
    assert "WRITE_SUCCEEDED" not in data["stdout"]


@pytest.mark.asyncio
async def test_no_docker_socket_access(async_client):
    """Verify that the Docker socket is not visible or accessible in the container."""
    payload = {
        "job_id": "test_docker_socket",
        "language": "python",
        "files": {
            "main.py": (
                "import os\n"
                "has_sock = os.path.exists('/var/run/docker.sock')\n"
                "print(f'DOCKER_SOCK:{has_sock}')\n"
            )
        },
    }

    response = await async_client.post("/jobs", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "DOCKER_SOCK:False" in data["stdout"]
