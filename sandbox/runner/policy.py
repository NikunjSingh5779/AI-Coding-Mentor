"""
Sandbox security policy with strict resource limits.
"""

from typing import Dict, Any


class SandboxPolicy:
    """Security policy for sandbox execution."""

    # Resource limits
    memory_limit = "128m"  # 128MB RAM
    cpu_limit = 0.5  # 50% of one CPU core
    max_processes = 32
    max_file_size = 10 * 1024 * 1024  # 10MB
    max_output_size = 1024 * 1024  # 1MB

    # Time limits
    default_timeout = 30  # seconds
    max_timeout = 60  # seconds

    # Network and filesystem
    network_disabled = True
    filesystem_readonly = True

    # Security features
    drop_capabilities = ["ALL"]
    no_new_privileges = True
    non_root_user = "sandbox:sandbox"

    @classmethod
    def get_docker_config(cls) -> Dict[str, Any]:
        """Get Docker container configuration based on policy."""
        return {
            "mem_limit": cls.memory_limit,
            "memswap_limit": cls.memory_limit,  # No swap
            "cpu_period": 100000,
            "cpu_quota": int(100000 * cls.cpu_limit),
            "network_disabled": cls.network_disabled,
            "read_only": cls.filesystem_readonly,
            "security_opt": ["no-new-privileges:true"],
            "cap_drop": cls.drop_capabilities,
            "user": cls.non_root_user,
            "pids_limit": cls.max_processes,
        }