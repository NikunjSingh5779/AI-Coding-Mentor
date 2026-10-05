"""
AI Coding Mentor — Sandbox Runner Service
Executes learner code safely in isolated containers with strict resource limits.
"""

import asyncio
import base64
import logging
import os
import time
from typing import Any, Dict, List, Optional

from fastapi import Depends, FastAPI, Header, HTTPException, status
from pydantic import BaseModel, Field
import docker
from docker.errors import APIError, ContainerError, ImageNotFound, NotFound

try:
    from runner.languages import get_language_config
    from runner.policy import JobLimits, SandboxPolicy
except ImportError:
    from languages import get_language_config
    from policy import JobLimits, SandboxPolicy

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("sandbox.runner")

# Environment settings
SANDBOX_SECRET = os.getenv("SANDBOX_SECRET", "mentor-sandbox-secret-dev")

# Concurrency semaphore for P-09 (2 concurrent jobs max)
concurrency_semaphore = asyncio.Semaphore(SandboxPolicy.max_concurrent_jobs)


# Request and Response Models
class TestCaseSpec(BaseModel):
    """Specification of a test case for execution."""
    id: str = Field(default="")
    stdin: str = Field(default="")
    expected_output: Optional[str] = Field(default=None)
    is_hidden: bool = Field(default=False)


class TestCaseResult(BaseModel):
    """Outcome of a single test case execution."""
    id: str
    passed: bool
    stdout: str
    stderr: str
    exit_code: int
    duration_ms: float
    is_hidden: bool = False
    error_type: Optional[str] = None


class JobLimitsSpec(BaseModel):
    """Customizable resource limits for a job."""
    timeout_seconds: Optional[float] = Field(default=5.0)
    memory_mb: Optional[int] = Field(default=256)
    max_processes: Optional[int] = Field(default=64)


class JobRequest(BaseModel):
    """Request to execute a code job."""
    job_id: str = Field(default_factory=lambda: f"job_{int(time.time() * 1000)}")
    language: str = Field(default="python")
    files: Dict[str, str] = Field(default_factory=dict)
    stdin: str = Field(default="")
    mode: str = Field(default="run")  # "compile", "run", "test"
    tests: Optional[List[TestCaseSpec]] = None
    limits: Optional[JobLimitsSpec] = None


class JobResult(BaseModel):
    """Result of a code execution job."""
    job_id: str
    status: str  # "success", "error", "timeout", "memory_limit", "busy"
    exit_code: int
    stdout: str
    stderr: str
    duration_ms: float
    truncated: bool = False
    timings: Dict[str, float] = Field(default_factory=dict)
    test_results: Optional[List[TestCaseResult]] = None


# Legacy compatibility models
class LegacyExecutionRequest(BaseModel):
    code: str
    language: str = "python"
    stdin: str = ""
    timeout: int = 5


class LegacyExecutionResult(BaseModel):
    success: bool
    stdout: str
    stderr: str
    exit_code: int
    execution_time: float
    error_type: Optional[str] = None


# Authentication dependency
async def verify_sandbox_secret(
    x_sandbox_secret: Optional[str] = Header(None),
    authorization: Optional[str] = Header(None),
):
    """Verify shared secret authentication."""
    if not SANDBOX_SECRET:
        return True

    provided_secret = x_sandbox_secret
    if not provided_secret and authorization:
        if authorization.startswith("Bearer "):
            provided_secret = authorization[7:].strip()
        else:
            provided_secret = authorization.strip()

    # In local development mode, if secret is default, allow requests
    if SANDBOX_SECRET in ("mentor-sandbox-secret-dev", "development") and not provided_secret:
        return True

    if provided_secret != SANDBOX_SECRET:
        logger.warning("Unauthorized access attempt to sandbox runner")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing sandbox authentication secret",
        )
    return True


class DockerSandboxManager:
    """Manages Docker container creation, file streaming, and process monitoring."""

    def __init__(self):
        try:
            self.client = docker.from_env()
        except Exception as e:
            logger.warning(f"Docker client initialization failed: {e}. Runner may operate in fallback mode.")
            self.client = None

    def build_shell_command(
        self,
        files: Dict[str, str],
        stdin_data: str,
        lang_config: Dict[str, Any],
    ) -> List[str]:
        """Build a safe in-container shell script to populate /work tmpfs and execute."""
        setup_cmds = []

        for fname, content in files.items():
            safe_fname = os.path.basename(fname)
            b64_content = base64.b64encode(content.encode("utf-8")).decode("ascii")
            setup_cmds.append(f"printf '%s' '{b64_content}' | base64 -d > /work/{safe_fname}")

        b64_stdin = base64.b64encode(stdin_data.encode("utf-8")).decode("ascii")
        setup_cmds.append(f"printf '%s' '{b64_stdin}' | base64 -d > /work/stdin.txt")

        main_file = lang_config.get("filename", "main.py")
        setup_cmds.append(f"exec python3 -u /work/{main_file} < /work/stdin.txt")

        return ["/bin/sh", "-c", " && ".join(setup_cmds)]

    async def run_single_job(
        self,
        files: Dict[str, str],
        stdin_data: str,
        lang_config: Dict[str, Any],
        limits: JobLimits,
    ) -> Dict[str, Any]:
        """Execute a single container job inside a hardened container."""
        if not self.client:
            raise RuntimeError("Docker daemon is not available.")

        t_start = time.perf_counter()
        image_name = lang_config.get("image", "coding-mentor-python:latest")

        # Verify image or fallback
        try:
            self.client.images.get(image_name)
        except ImageNotFound:
            fallback = lang_config.get("fallback_image", "ai-screener-sandbox:latest")
            try:
                self.client.images.get(fallback)
                image_name = fallback
            except ImageNotFound:
                raise RuntimeError(f"Sandbox Docker image '{image_name}' not found. Run 'make sandbox-build'.")

        shell_cmd = self.build_shell_command(files, stdin_data, lang_config)

        docker_kwargs = SandboxPolicy.get_docker_config(limits)
        docker_kwargs.update({
            "image": image_name,
            "command": shell_cmd,
            "working_dir": "/work",
            "detach": True,
        })

        container = None
        setup_time = time.perf_counter() - t_start

        try:
            # Create and start container
            t_exec_start = time.perf_counter()
            loop = asyncio.get_event_loop()
            container = await loop.run_in_executor(
                None, lambda: self.client.containers.run(**docker_kwargs)
            )

            # Wait for execution with timeout
            timeout_sec = min(limits.timeout_seconds, SandboxPolicy.max_allowed_timeout)

            try:
                wait_res = await asyncio.wait_for(
                    loop.run_in_executor(None, container.wait),
                    timeout=timeout_sec,
                )
                exit_code = wait_res.get("StatusCode", -1)
                is_timeout = False
            except asyncio.TimeoutError:
                is_timeout = True
                exit_code = -1
                try:
                    await loop.run_in_executor(None, container.kill)
                except Exception:
                    pass

            exec_time = time.perf_counter() - t_exec_start

            # Read logs
            logs_stdout = ""
            logs_stderr = ""
            if not is_timeout:
                try:
                    logs_stdout = await loop.run_in_executor(
                        None, lambda: container.logs(stdout=True, stderr=False).decode("utf-8", errors="replace")
                    )
                    logs_stderr = await loop.run_in_executor(
                        None, lambda: container.logs(stdout=False, stderr=True).decode("utf-8", errors="replace")
                    )
                except Exception as e:
                    logs_stderr = f"Log extraction error: {e}"

            # Output truncation per P-08 (64 KB cap)
            max_out = limits.max_output_size
            truncated = False
            if len(logs_stdout) > max_out:
                logs_stdout = logs_stdout[:max_out] + "\n... [output truncated at 64 KB limit]"
                truncated = True
            if len(logs_stderr) > max_out:
                logs_stderr = logs_stderr[:max_out] + "\n... [output truncated at 64 KB limit]"
                truncated = True

            # Determine status
            if is_timeout:
                status_str = "timeout"
                logs_stderr = f"Execution timed out after {timeout_sec:.1f} seconds"
            elif exit_code == 137:
                status_str = "memory_limit"
                logs_stderr = "Process killed (Memory limit exceeded / OOM)"
            elif exit_code == 0:
                status_str = "success"
            else:
                status_str = "error"

            total_duration_ms = (time.perf_counter() - t_start) * 1000.0

            return {
                "status": status_str,
                "exit_code": exit_code,
                "stdout": logs_stdout,
                "stderr": logs_stderr,
                "duration_ms": round(total_duration_ms, 2),
                "truncated": truncated,
                "timings": {
                    "setup_ms": round(setup_time * 1000.0, 2),
                    "execution_ms": round(exec_time * 1000.0, 2),
                },
            }

        finally:
            if container:
                try:
                    await loop.run_in_executor(None, lambda: container.remove(force=True))
                except Exception:
                    pass


docker_manager = DockerSandboxManager()

# FastAPI application
app = FastAPI(
    title="AI Coding Mentor — Sandbox Runner",
    description="Isolated code execution engine with P-08/P-09 resource and security constraints.",
    version="0.1.0",
)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    docker_ok = docker_manager.client is not None
    return {
        "status": "healthy" if docker_ok else "degraded",
        "service": "sandbox-runner",
        "docker_available": docker_ok,
    }


@app.post("/jobs", response_model=JobResult, dependencies=[Depends(verify_sandbox_secret)])
async def execute_job(request: JobRequest):
    """
    Execute a code job with strict isolation and resource bounds.
    """
    # Check language configuration
    lang_config = get_language_config(request.language)
    if not lang_config:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported language '{request.language}'",
        )

    # Prepare files
    files = dict(request.files)
    if not files:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Job files dictionary cannot be empty",
        )

    # Validate file sizes (max 100 KB total per request P-10)
    total_size = sum(len(c) for c in files.values())
    if total_size > 100_000:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Total code size exceeds 100 KB limit",
        )

    # Configure limits
    limits = JobLimits()
    if request.limits:
        if request.limits.timeout_seconds is not None:
            limits.timeout_seconds = min(request.limits.timeout_seconds, SandboxPolicy.max_allowed_timeout)
        if request.limits.memory_mb is not None:
            limits.memory_limit = f"{request.limits.memory_mb}m"
        if request.limits.max_processes is not None:
            limits.max_processes = request.limits.max_processes

    # Concurrency control (P-09)
    try:
        acquired = await asyncio.wait_for(concurrency_semaphore.acquire(), timeout=0.05)
    except asyncio.TimeoutError:
        logger.warning(f"Runner concurrency limit ({SandboxPolicy.max_concurrent_jobs}) reached for job {request.job_id}")
        return JobResult(
            job_id=request.job_id,
            status="busy",
            exit_code=-1,
            stdout="",
            stderr="Runner busy: concurrency limit reached. Please retry in a moment.",
            duration_ms=0.0,
            truncated=False,
        )

    try:
        # Mode: Test execution vs Single run
        if request.mode == "test" and request.tests:
            test_results: List[TestCaseResult] = []
            overall_status = "success"
            first_exit_code = 0
            all_stdout = []
            all_stderr = []
            total_duration = 0.0

            for test in request.tests:
                res = await docker_manager.run_single_job(
                    files=files,
                    stdin_data=test.stdin,
                    lang_config=lang_config,
                    limits=limits,
                )

                duration_ms = res["duration_ms"]
                total_duration += duration_ms

                # Compare output after stripping trailing whitespace
                actual_stdout = res["stdout"]
                passed = False
                if res["exit_code"] == 0:
                    if test.expected_output is not None:
                        passed = (actual_stdout.rstrip() == test.expected_output.rstrip())
                    else:
                        passed = True
                else:
                    if overall_status == "success":
                        overall_status = res["status"]
                        first_exit_code = res["exit_code"]

                if not passed and overall_status == "success":
                    overall_status = "error"

                test_results.append(
                    TestCaseResult(
                        id=test.id,
                        passed=passed,
                        stdout=actual_stdout,
                        stderr=res["stderr"],
                        exit_code=res["exit_code"],
                        duration_ms=duration_ms,
                        is_hidden=test.is_hidden,
                        error_type=None if res["exit_code"] == 0 else res["status"],
                    )
                )

            return JobResult(
                job_id=request.job_id,
                status=overall_status,
                exit_code=first_exit_code,
                stdout="\n".join(all_stdout),
                stderr="\n".join(all_stderr),
                duration_ms=round(total_duration, 2),
                test_results=test_results,
            )

        else:
            # Mode: Single execution ("run" or "compile")
            res = await docker_manager.run_single_job(
                files=files,
                stdin_data=request.stdin,
                lang_config=lang_config,
                limits=limits,
            )

            return JobResult(
                job_id=request.job_id,
                status=res["status"],
                exit_code=res["exit_code"],
                stdout=res["stdout"],
                stderr=res["stderr"],
                duration_ms=res["duration_ms"],
                truncated=res["truncated"],
                timings=res["timings"],
            )

    finally:
        concurrency_semaphore.release()


# Legacy /execute compatibility endpoint
@app.post("/execute", response_model=LegacyExecutionResult)
async def legacy_execute(request: LegacyExecutionRequest):
    """Backwards-compatible execution endpoint."""
    lang_config = get_language_config(request.language) or get_language_config("python")
    filename = lang_config.get("filename", "main.py")

    job_req = JobRequest(
        language=request.language,
        files={filename: request.code},
        stdin=request.stdin,
        limits=JobLimitsSpec(timeout_seconds=float(request.timeout)),
    )

    job_res = await execute_job(job_req)
    return LegacyExecutionResult(
        success=(job_res.status == "success" and job_res.exit_code == 0),
        stdout=job_res.stdout,
        stderr=job_res.stderr,
        exit_code=job_res.exit_code,
        execution_time=job_res.duration_ms / 1000.0,
        error_type=None if job_res.status == "success" else job_res.status,
    )
