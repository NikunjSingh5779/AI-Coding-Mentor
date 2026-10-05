"""
Sandbox security policy with strict resource limits per P-08 and P-09.
"""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional


@dataclass
class JobLimits:
    """Per-job resource and execution limits."""
    timeout_seconds: float = 5.0
    memory_limit: str = "256m"
    cpu_limit: float = 1.0
    max_processes: int = 64
    max_file_size: int = 10 * 1024 * 1024  # 10 MB
    max_output_size: int = 64 * 1024       # 64 KB (P-08)


class SandboxPolicy:
    """Security policy and container flags for the sandbox runner."""

    # Baseline P-08 limits
    default_limits = JobLimits(
        timeout_seconds=5.0,
        memory_limit="256m",
        cpu_limit=1.0,
        max_processes=64,
        max_file_size=10 * 1024 * 1024,
        max_output_size=64 * 1024,
    )

    # Concurrency limit P-09
    max_concurrent_jobs = 2

    # Hard ceiling limits
    max_allowed_timeout = 10.0
    max_allowed_memory = "512m"

    # Isolation flags
    network_disabled = True
    filesystem_readonly = True
    drop_capabilities: List[str] = ["ALL"]
    no_new_privileges = True
    non_root_user = "1000:1000"
    workdir_tmpfs_config = "rw,nosuid,size=32m,uid=1000,gid=1000,mode=1777"

    @classmethod
    def get_docker_config(cls, limits: Optional[JobLimits] = None) -> Dict[str, Any]:
        """Generate Docker container run kwargs based on policy and limits."""
        effective_limits = limits or cls.default_limits

        # Enforce maximum timeout bounds
        timeout = min(effective_limits.timeout_seconds, cls.max_allowed_timeout)
        if timeout <= 0:
            timeout = cls.default_limits.timeout_seconds

        return {
            "mem_limit": effective_limits.memory_limit,
            "memswap_limit": effective_limits.memory_limit,  # Strict: no swap
            "cpu_period": 100000,
            "cpu_quota": int(100000 * effective_limits.cpu_limit),
            "network_disabled": cls.network_disabled,
            "read_only": cls.filesystem_readonly,
            "security_opt": ["no-new-privileges:true"],
            "cap_drop": cls.drop_capabilities,
            "user": cls.non_root_user,
            "pids_limit": effective_limits.max_processes,
            "tmpfs": {"/work": cls.workdir_tmpfs_config},
            "environment": {
                "PYTHONUNBUFFERED": "1",
                "PYTHONDONTWRITEBYTECODE": "1",
            },
        }
