"""Docker-backed sandbox executor.

The API never receives the Docker socket. Only the dedicated sandbox service
uses it. Containers run with no network, dropped capabilities, a read-only
root filesystem and bounded CPU/memory/PIDs/output.
"""

from __future__ import annotations

import asyncio
import tempfile
from pathlib import Path

import docker
from docker.errors import APIError, DockerException, ImageNotFound

from app.execution.policy import (
    LANGUAGE_COMMANDS,
    LANGUAGE_IMAGES,
    ExecutionPolicy,
)


class SandboxUnavailable(RuntimeError):
    """Raised when the sandbox service cannot execute a request."""


class SandboxExecutor:
    def __init__(self, policy: ExecutionPolicy | None = None) -> None:
        self.policy = policy or ExecutionPolicy()

    async def execute(
        self,
        code: str,
        language: str,
        stdin: str = "",
        timeout_seconds: int | None = None,
    ) -> dict:
        language = language.lower().strip()
        if language not in LANGUAGE_IMAGES:
            raise ValueError(f"Unsupported language: {language}")

        if len(code.encode("utf-8")) > self.policy.max_code_bytes:
            raise ValueError("Code exceeds maximum size")

        timeout = max(
            1,
            min(
                timeout_seconds or self.policy.timeout_seconds,
                self.policy.max_timeout_seconds,
            ),
        )

        return await asyncio.to_thread(
            self._execute_sync,
            code,
            language,
            stdin,
            timeout,
        )

    def _execute_sync(
        self, code: str, language: str, stdin: str, timeout: int
    ) -> dict:
        try:
            client = docker.from_env()
        except DockerException as exc:
            raise SandboxUnavailable("Docker is unavailable") from exc

        filename, command = LANGUAGE_COMMANDS[language]
        image = LANGUAGE_IMAGES[language]

        with tempfile.TemporaryDirectory(prefix="mentor-exec-") as tmp:
            root = Path(tmp)
            (root / filename).write_text(code, encoding="utf-8")
            (root / "stdin.txt").write_text(stdin, encoding="utf-8")

            try:
                client.images.get(image)
            except ImageNotFound as exc:
                raise SandboxUnavailable(
                    f"Sandbox image is not built: {image}"
                ) from exc

            full_command = f"{command} < /workspace/stdin.txt"
            container = None
            try:
                container = client.containers.run(
                    image=image,
                    command=["sh", "-lc", full_command],
                    working_dir="/workspace",
                    volumes={str(root): {"bind": "/workspace", "mode": "ro"}},
                    network_disabled=True,
                    read_only=True,
                    security_opt=["no-new-privileges:true"],
                    cap_drop=["ALL"],
                    mem_limit=self.policy.memory_bytes,
                    memswap_limit=self.policy.memory_bytes,
                    cpu_period=100000,
                    cpu_quota=max(1, int(100000 * self.policy.cpu_limit)),
                    pids_limit=self.policy.pids_limit,
                    tmpfs={
                        "/tmp": "rw,noexec,nosuid,nodev,size=32m",
                    },
                    environment={
                        "PYTHONUNBUFFERED": "1",
                        "PYTHONDONTWRITEBYTECODE": "1",
                        "HOME": "/tmp",
                    },
                    user="sandbox:sandbox",
                    stdin_open=False,
                    detach=True,
                    remove=True,
                )

                try:
                    wait = container.wait(timeout=timeout)
                except Exception as exc:
                    try:
                        container.kill()
                    except Exception:
                        pass
                    return {
                        "success": False,
                        "stdout": "",
                        "stderr": f"Execution timed out after {timeout}s",
                        "exit_code": -1,
                        "execution_time_ms": timeout * 1000,
                        "error_type": "TIMEOUT",
                    }

                status = int(wait.get("StatusCode", 1))
                stdout = container.logs(
                    stdout=True, stderr=False
                ).decode("utf-8", errors="replace")
                stderr = container.logs(
                    stdout=False, stderr=True
                ).decode("utf-8", errors="replace")

                truncated = False
                max_bytes = self.policy.max_output_bytes
                if len(stdout.encode("utf-8")) > max_bytes:
                    stdout = stdout.encode("utf-8")[:max_bytes].decode(
                        "utf-8", errors="replace"
                    )
                    truncated = True
                if len(stderr.encode("utf-8")) > max_bytes:
                    stderr = stderr.encode("utf-8")[:max_bytes].decode(
                        "utf-8", errors="replace"
                    )
                    truncated = True

                return {
                    "success": status == 0,
                    "stdout": stdout,
                    "stderr": stderr,
                    "exit_code": status,
                    "execution_time_ms": 0,
                    "error_type": "OUTPUT_TRUNCATED" if truncated else None,
                }
            except APIError as exc:
                raise SandboxUnavailable(str(exc)) from exc
            finally:
                client.close()
