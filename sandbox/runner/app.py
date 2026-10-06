"""Dedicated sandbox HTTP service.

Only this service accesses the Docker socket. The application API talks to it
over HTTP, keeping Docker privileges out of the API container.
"""

from __future__ import annotations

import asyncio
import tempfile
import time
from pathlib import Path

import docker
from docker.errors import APIError, DockerException, ImageNotFound
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from languages import LANGUAGE_COMMANDS, LANGUAGE_IMAGES


class ExecutionRequest(BaseModel):
    code: str = Field(..., max_length=250_000)
    language: str = Field(..., min_length=1, max_length=32)
    stdin: str = Field(default="", max_length=50_000)
    timeout: int = Field(default=30, ge=1, le=60)


class ExecutionResult(BaseModel):
    success: bool
    stdout: str
    stderr: str
    exit_code: int
    execution_time_ms: int
    error_type: str | None = None


class SandboxRunner:
    def __init__(self) -> None:
        self.policy = {
            "memory": 256 * 1024 * 1024,
            "pids": 64,
            "max_output": 1_048_576,
        }
        try:
            self.client = docker.from_env()
            self.startup_error = None
        except DockerException as exc:
            self.client = None
            self.startup_error = str(exc)

    async def execute(self, request: ExecutionRequest) -> ExecutionResult:
        if request.language.lower() not in LANGUAGE_IMAGES:
            raise HTTPException(400, "Unsupported language")
        if self.client is None:
            raise HTTPException(503, "Docker is unavailable to sandbox runner")
        return await asyncio.to_thread(self._execute_sync, request)

    def _execute_sync(self, request: ExecutionRequest) -> ExecutionResult:
        language = request.language.lower()
        image = LANGUAGE_IMAGES[language]
        filename, command = LANGUAGE_COMMANDS[language]
        started = time.perf_counter()

        with tempfile.TemporaryDirectory(prefix="mentor-sandbox-") as tmp:
            root = Path(tmp)
            (root / filename).write_text(request.code, encoding="utf-8")
            (root / "stdin.txt").write_text(request.stdin, encoding="utf-8")

            try:
                self.client.images.get(image)
            except ImageNotFound as exc:
                raise HTTPException(
                    503, f"Sandbox image is unavailable: {image}"
                ) from exc

            container = None
            try:
                container = self.client.containers.run(
                    image=image,
                    command=["sh", "-lc", f"{command} < /workspace/stdin.txt"],
                    working_dir="/workspace",
                    volumes={str(root): {"bind": "/workspace", "mode": "ro"}},
                    network_disabled=True,
                    read_only=True,
                    security_opt=["no-new-privileges:true"],
                    cap_drop=["ALL"],
                    mem_limit=self.policy["memory"],
                    memswap_limit=self.policy["memory"],
                    cpu_period=100000,
                    cpu_quota=50000,
                    pids_limit=self.policy["pids"],
                    tmpfs={"/tmp": "rw,noexec,nosuid,nodev,size=32m"},
                    environment={
                        "PYTHONUNBUFFERED": "1",
                        "PYTHONDONTWRITEBYTECODE": "1",
                        "HOME": "/tmp",
                        "PATH": "/usr/local/bin:/usr/bin:/bin",
                    },
                    user="sandbox:sandbox",
                    detach=True,
                )

                try:
                    status = int(container.wait(timeout=request.timeout).get("StatusCode", 1))
                except Exception:
                    try:
                        container.kill()
                    except Exception:
                        pass
                    return ExecutionResult(
                        success=False,
                        stdout="",
                        stderr=f"Execution timed out after {request.timeout}s",
                        exit_code=-1,
                        execution_time_ms=request.timeout * 1000,
                        error_type="TIMEOUT",
                    )

                stdout = container.logs(stdout=True, stderr=False).decode(
                    "utf-8", errors="replace"
                )
                stderr = container.logs(stdout=False, stderr=True).decode(
                    "utf-8", errors="replace"
                )
                truncated = False
                limit = self.policy["max_output"]
                if len(stdout.encode()) > limit:
                    stdout = stdout.encode()[:limit].decode("utf-8", errors="replace")
                    truncated = True
                if len(stderr.encode()) > limit:
                    stderr = stderr.encode()[:limit].decode("utf-8", errors="replace")
                    truncated = True

                return ExecutionResult(
                    success=status == 0,
                    stdout=stdout,
                    stderr=stderr,
                    exit_code=status,
                    execution_time_ms=int((time.perf_counter() - started) * 1000),
                    error_type="OUTPUT_TRUNCATED" if truncated else None,
                )
            except APIError as exc:
                raise HTTPException(503, str(exc)) from exc
            finally:
                if container is not None:
                    try:
                        container.remove(force=True)
                    except Exception:
                        pass


app = FastAPI(title="AI Coding Mentor Sandbox Runner", version="1.0.0")
runner = SandboxRunner()


@app.post("/execute", response_model=ExecutionResult)
async def execute_code(request: ExecutionRequest) -> ExecutionResult:
    return await runner.execute(request)


@app.get("/health")
async def health() -> dict[str, str]:
    return {
        "status": "healthy" if runner.client is not None else "degraded",
        "service": "sandbox-runner",
    }
