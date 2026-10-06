import docker
import pytest

@pytest.mark.isolation
def test_python_runtime_disallows_network():
    client = docker.from_env()
    container = None
    try:
        container = client.containers.run(
            image='coding-mentor-python:ci',
            command=['python', '-c', "import socket; socket.create_connection(('1.1.1.1', 53), 1)"],
            network_disabled=True,
            read_only=True,
            security_opt=['no-new-privileges:true'],
            cap_drop=['ALL'],
            mem_limit=64 * 1024 * 1024,
            memswap_limit=64 * 1024 * 1024,
            pids_limit=16,
            user='sandbox:sandbox',
            detach=True,
        )
        assert container.wait(timeout=5)['StatusCode'] != 0
    finally:
        if container is not None:
            container.remove(force=True)
        client.close()

@pytest.mark.isolation
def test_python_runtime_filesystem_is_read_only():
    client = docker.from_env()
    container = None
    try:
        container = client.containers.run(
            image='coding-mentor-python:ci',
            command=['python', '-c', "open('/workspace/blocked.txt', 'w').write('x')"],
            network_disabled=True,
            read_only=True,
            security_opt=['no-new-privileges:true'],
            cap_drop=['ALL'],
            mem_limit=64 * 1024 * 1024,
            memswap_limit=64 * 1024 * 1024,
            pids_limit=16,
            user='sandbox:sandbox',
            detach=True,
        )
        assert container.wait(timeout=5)['StatusCode'] != 0
    finally:
        if container is not None:
            container.remove(force=True)
        client.close()
