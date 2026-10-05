# AI Real-Time Coding Screener — Sandbox Runner

Safe containerized code execution service for the AI Coding Mentor.

## 1. Threat Model

Untrusted code submitted by learners may contain accidental infinite loops, resource exhaustion bugs, or intentional exploit attempts. The sandbox runner enforces defense-in-depth isolation between untrusted code, the runner process, the host system, and the API.

### 1.1 Assets & Security Objectives

| Asset | Threat | Security Control | Verification |
|---|---|---|---|
| **Host machine & filesystem** | Container escape, host file read/write, host command execution | User namespace remapping, non-root user (`sandbox:sandbox`, uid/gid 1000:1000), read-only root filesystem, dropped Linux capabilities (`ALL`), `no-new-privileges:true`, no host directory mounts. | Isolation test: host `/` and Docker socket inaccessible; rootfs write fails. |
| **Network & credentials** | Outbound SSRF, command & control, exfiltration of environment secrets | Docker network mode disabled (`--network none`). No network interfaces except local loopback. No sensitive environment variables passed to container. | Isolation test: socket creation / network connection fails immediately. |
| **Host CPU & Memory** | Fork bombs, memory exhaustion (OOM), infinite loops | Hard memory cap (`256m`), swap disabled (`--memory-swap 256m`), CPU quota (`--cpus 1.0`), PID limit (`--pids-limit 64`), wall-clock timeout watchdog (5s default, 10s max). | Limit test: fork bomb blocked, memory bomb killed with exit code 137, infinite loop killed at 5s. |
| **Disk & Output Volume** | Disk fill, stdout flood, pipe buffer overflow | `/work` on in-memory tmpfs (`size=32m,nosuid`), `ulimit fsize=10MB`, stdout/stderr output stream capped at 64 KB with `truncated=true` flag. | Limit test: 100MB output stream truncated cleanly to 64 KB. |
| **Cross-Session Privacy** | Code or state leakage between jobs or learners | Ephemeral single-use containers (`--rm`), fresh tmpfs per execution, no persistent disk state between runs. | Isolation test: files created in job N do not exist in job N+1. |
| **API & Runner Service** | Unauthorized execution requests | Shared-secret authentication (`SANDBOX_SECRET`), internal network isolation (service not exposed to public Internet). | Integration test: unauthenticated requests rejected with 401. |

### 1.2 Trust Boundaries

1. **Browser / Learner $\rightarrow$ Backend API:** Untrusted external clients. Input validation, length bounds, rate limits.
2. **Backend API $\rightarrow$ Sandbox Runner:** Internal network, authenticated by `SANDBOX_SECRET`. Runner accepts job specs and enforces concurrency limit (P-09). The API never mounts the Docker socket.
3. **Sandbox Runner $\rightarrow$ Docker Container:** Untrusted code executes inside hardened, isolated OCI containers.

---

## 2. Sandbox Security Policy (P-08 & P-09)

The sandbox runner enforces the following baseline configuration for every execution:

```text
network:         none (no external or internal network access)
root filesystem: read-only
work directory:  tmpfs /work (size=32m, nosuid, rw)
user:            sandbox:sandbox (uid 1000, gid 1000)
capabilities:    all dropped (--cap-drop ALL)
privileges:      no-new-privileges:true
processes:       pids_limit 64
memory:          256 MB hard limit, memory-swap 256 MB (no swap)
cpu:             1.0 CPU core (cpu_quota=100000, cpu_period=100000)
file limits:     fsize=10485760 (10MB max file size), nofile=64
time:            wall-clock watchdog timeout (5s default, 10s maximum)
output:          64 KB cap on combined stdout/stderr; excess discarded with truncated=true
lifecycle:       ephemeral container created per job and removed immediately upon completion
concurrency:     max 2 concurrent execution jobs (P-09); excess requests return 429 / runner_busy
```

---

## 3. Runner API Specification

### `POST /jobs`
Submits a code execution job.

#### Headers
- `X-Sandbox-Secret: <SANDBOX_SECRET>` (or `Authorization: Bearer <SANDBOX_SECRET>`)

#### Request Body (`JobRequest`)
```json
{
  "job_id": "job_12345678",
  "language": "python",
  "files": {
    "main.py": "print('Hello, world!')"
  },
  "stdin": "",
  "mode": "run",
  "limits": {
    "timeout_seconds": 5,
    "memory_mb": 256
  }
}
```

#### Response Body (`JobResult`)
```json
{
  "job_id": "job_12345678",
  "status": "success",
  "exit_code": 0,
  "stdout": "Hello, world!\n",
  "stderr": "",
  "duration_ms": 42.5,
  "truncated": false,
  "timings": {
    "setup_ms": 2.1,
    "execution_ms": 40.4
  }
}
```

Possible statuses:
- `success`: Process ran and exited with status 0.
- `error`: Process exited with non-zero exit code (traceback / runtime exception).
- `timeout`: Execution exceeded wall-clock timeout and container was killed.
- `memory_limit`: Process exceeded memory cap (killed with SIGKILL / exit code 137).
- `busy`: Concurrency limit reached; caller should retry or back off.

---

## 4. Building and Running

### Build the Python Sandbox Container
```bash
docker build -t coding-mentor-python:latest -f images/python/Dockerfile .
```

### Run the Runner Service (Local / Dev)
```bash
uv run uvicorn runner.app:app --host 0.0.0.0 --port 8100
```

### Run Sandbox Test Suite
```bash
pytest tests/ -v
```
