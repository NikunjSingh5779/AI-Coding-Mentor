# ADR-0006: Sandbox Isolation and Execution Architecture

**Date:** 2026-10-05  
**Status:** Accepted  
**Phase:** PH3 — Sandbox and Execution  
**Decision Driver:** Q5 (Single-user local vs hosted deployment)

---

## Context

Phase 3 introduces execution of untrusted learner code and automated test verification. Untrusted code submitted by learners may contain accidental infinite loops, memory leaks, fork bombs, or malicious attempts to read host files, make network requests, or exhaust machine resources.

Per ADR-0002 (Q5 resolution), the system operates primarily as a single-user local application for demonstration, viva, and personal mentoring. However, the architecture must guarantee that:
1. Learner code never runs directly in the API process.
2. The API process never mounts the host Docker socket.
3. Untrusted code is strictly contained with deterministic resource and time limits.
4. A clear path exists for upgrading to multi-tenant or cloud-hosted deployments.

---

## Decision

### 1. Isolation Mechanism for Local Single-User Deployment (Q5 = A)
For the current single-user local deployment, we implement **Hardened OCI/Docker Container Isolation** managed by a dedicated in-process or containerized runner service (`sandbox/runner/`):

- **Non-Root Execution:** Container runs strictly as `sandbox:sandbox` (UID 1000, GID 1000).
- **Network Isolation:** `--network none` (no external or internal network interfaces; only loopback).
- **Filesystem Security:** Read-only root filesystem (`--read-only`), ephemeral in-memory tmpfs mount for workspace (`--tmpfs /work:rw,nosuid,size=32m`).
- **Privilege Stripping:** `--cap-drop ALL`, `--security-opt no-new-privileges:true`.
- **Resource Constraints (P-08):**
  - CPU: `--cpus 1.0` (100% of 1 core max).
  - Memory: `--memory 256m --memory-swap 256m` (strict 256 MB cap, no swap).
  - Process Limit: `--pids-limit 64` (mitigates fork bombs).
  - File Size: `ulimit fsize=10485760` (10 MB max file creation).
- **Time Watchdog:** Runner enforces wall-clock timeouts (default 5.0s, hard cap 10.0s) and explicitly kills and removes hung containers.
- **Output Capping:** Stdout and stderr streams are capped at 64 KB total with a `truncated: true` flag.
- **Concurrency Gate (P-09):** Concurrency limit of 2 simultaneous jobs to prevent local CPU starvation; additional requests return `429 / runner_busy`.

### 2. Architecture for Multi-Tenant / Hosted Environments (Q5 = B Upgrade Path)
Containers share the host Linux kernel. If the application is upgraded to a multi-tenant cloud environment with untrusted external users, container isolation will be swapped behind the same runner interface (`POST /jobs`) with:
- **gVisor (`runsc`):** An application kernel written in Go that intercepts system calls and isolates untrusted code from the host Linux kernel.
- **MicroVMs (Firecracker / Kata):** Hardware-level virtualization with sub-second boot times.
- **Managed Execution Engines:** E.g., Judge0 or isolated serverless runners.

Because the API communicates with the sandbox solely over an HTTP JSON interface (`POST /jobs`), the backend API remains decoupled from the underlying container runtime.

### 3. Test Runner & Information Hiding (Q3)
- Public test cases display inputs, actual output, and expected output.
- Hidden test cases (`is_hidden: true`) display pass/fail status only; their input parameters and expected output are never serialized or transmitted to the client.
- Trailing whitespace is normalized during output comparison to prevent trivial false-negative mismatches.

---

## Consequences

- **Safety:** The host system and API server are protected against rogue processes, resource exhaustion, and network exfiltration.
- **Portability:** Docker/OCI containers run consistently across Windows (via WSL2), macOS, and Linux.
- **Extensibility:** Additional language environments (such as C++ or Java in Phase 8) use the same runner contract and security policy.
