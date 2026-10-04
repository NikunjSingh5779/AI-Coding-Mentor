"""
Python sandbox runner application.
Executes learner code safely in isolated containers with strict resource limits.
"""

import asyncio
import json
import logging
import os
import tempfile
import time
from typing import Dict, Any, Optional
from pathlib import Path

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
import docker
from docker.errors import ContainerError, ImageNotFound

from languages import get_language_config
from policy import SandboxPolicy

logger = logging.getLogger(__name__)

# Request/Response models
class ExecutionRequest(BaseModel):
    """Request to execute code in the sandbox."""
    code: str = Field(..., description="Code to execute")
    language: str = Field(..., description="Programming language")
    stdin: str = Field(default="", description="Standard input for the program")
    timeout: int = Field(default=30, description="Execution timeout in seconds")


class ExecutionResult(BaseModel):
    """Result from code execution."""
    success: bool
    stdout: str
    stderr: str
    exit_code: int
    execution_time: float
    memory_used: Optional[int] = None
    error_type: Optional[str] = None


class SandboxRunner:
    """Manages code execution in Docker containers."""

    def __init__(self):
        self.client = docker.from_env()
        self.policy = SandboxPolicy()
        self._ensure_images()

    def _ensure_images(self):
        """Ensure all language images are built."""
        for lang in ["python", "java", "cpp"]:
            image_name = f"coding-mentor-{lang}:latest"
            try:
                self.client.images.get(image_name)
                logger.info(f"Found image {image_name}")
            except ImageNotFound:
                logger.warning(f"Image {image_name} not found - build with 'make sandbox-build'")

    async def execute(self, request: ExecutionRequest) -> ExecutionResult:
        """Execute code safely in a container."""
        start_time = time.time()

        try:
            # Get language configuration
            lang_config = get_language_config(request.language)
            if not lang_config:
                raise ValueError(f"Unsupported language: {request.language}")

            # Create temporary directory for code
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_path = Path(temp_dir)

                # Write code to file
                code_file = temp_path / lang_config["filename"]
                code_file.write_text(request.code, encoding="utf-8")

                # Write stdin if provided
                stdin_file = temp_path / "stdin.txt"
                if request.stdin:
                    stdin_file.write_text(request.stdin, encoding="utf-8")

                # Execute in container
                result = await self._run_container(
                    lang_config, temp_path, request.timeout
                )

                execution_time = time.time() - start_time
                result.execution_time = execution_time

                return result

        except Exception as e:
            logger.exception("Execution failed", extra={
                "language": request.language,
                "error": str(e)
            })

            return ExecutionResult(
                success=False,
                stdout="",
                stderr=f"Execution error: {str(e)}",
                exit_code=-1,
                execution_time=time.time() - start_time,
                error_type=type(e).__name__
            )

    async def _run_container(
        self,
        lang_config: Dict[str, Any],
        code_dir: Path,
        timeout: int
    ) -> ExecutionResult:
        """Run code in a Docker container with safety limits."""

        image_name = f"coding-mentor-{lang_config['name']}:latest"

        # Container configuration
        container_config = {
            "image": image_name,
            "command": lang_config["run_command"],
            "working_dir": "/workspace",
            "volumes": {
                str(code_dir): {"bind": "/workspace", "mode": "ro"}
            },
            "mem_limit": self.policy.memory_limit,
            "memswap_limit": self.policy.memory_limit,  # No swap
            "cpu_period": 100000,
            "cpu_quota": int(100000 * self.policy.cpu_limit),
            "network_disabled": True,
            "read_only": True,
            "security_opt": ["no-new-privileges:true"],
            "cap_drop": ["ALL"],
            "user": "sandbox:sandbox",
            "pids_limit": self.policy.max_processes,
            "ulimits": [
                docker.types.Ulimit(name="nproc", soft=self.policy.max_processes, hard=self.policy.max_processes),
                docker.types.Ulimit(name="nofile", soft=64, hard=64),
                docker.types.Ulimit(name="fsize", soft=self.policy.max_file_size, hard=self.policy.max_file_size),
            ],
            "environment": {
                "PYTHONUNBUFFERED": "1",
                "PYTHONDONTWRITEBYTECODE": "1"
            },
            "detach": True,
            "remove": True
        }

        try:
            # Run container
            container = self.client.containers.run(**container_config)

            # Wait for completion with timeout
            try:
                exit_code = container.wait(timeout=timeout)["StatusCode"]

                # Get logs
                logs = container.logs(stdout=True, stderr=True).decode("utf-8", errors="replace")

                # Split stdout/stderr (simple approach)
                stdout = logs
                stderr = ""

                return ExecutionResult(
                    success=(exit_code == 0),
                    stdout=stdout,
                    stderr=stderr,
                    exit_code=exit_code,
                    execution_time=0  # Will be set by caller
                )

            except Exception as e:
                # Timeout or other error
                try:
                    container.kill()
                except:
                    pass  # Container might already be dead

                if "timeout" in str(e).lower():
                    return ExecutionResult(
                        success=False,
                        stdout="",
                        stderr=f"Execution timed out after {timeout} seconds",
                        exit_code=-1,
                        execution_time=0,
                        error_type="TimeoutError"
                    )
                else:
                    raise

        except ContainerError as e:
            return ExecutionResult(
                success=False,
                stdout="",
                stderr=f"Container error: {e.stderr.decode('utf-8', errors='replace') if e.stderr else str(e)}",
                exit_code=e.exit_status,
                execution_time=0,
                error_type="ContainerError"
            )


# FastAPI app
app = FastAPI(
    title="AI Coding Mentor Sandbox",
    description="Safe code execution service",
    version="0.1.0"
)

runner = SandboxRunner()


@app.post("/execute", response_model=ExecutionResult)
async def execute_code(request: ExecutionRequest):
    """Execute code safely in a sandbox."""

    # Validate timeout
    if request.timeout > 60:
        raise HTTPException(
            status_code=400,
            detail="Timeout cannot exceed 60 seconds"
        )

    # Validate code size
    if len(request.code) > 100_000:  # 100KB
        raise HTTPException(
            status_code=400,
            detail="Code size cannot exceed 100KB"
        )

    return await runner.execute(request)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "sandbox-runner"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=8001,
        log_level="info"
    )