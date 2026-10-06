import pytest

from runner.policy import (
    CPU_QUOTA,
    DROP_CAPABILITIES,
    MAX_OUTPUT_BYTES,
    MAX_TIMEOUT_SECONDS,
    MEMORY_BYTES,
    NETWORK_DISABLED,
    NO_NEW_PRIVILEGES,
    NON_ROOT_USER,
    ROOT_FILESYSTEM_READONLY,
)


@pytest.mark.limits
def test_resource_limits_are_bounded() -> None:
    assert MEMORY_BYTES <= 256 * 1024 * 1024
    assert CPU_QUOTA <= 50_000
    assert MAX_OUTPUT_BYTES <= 1_048_576
    assert MAX_TIMEOUT_SECONDS <= 60


@pytest.mark.isolation
def test_isolation_policy() -> None:
    assert NETWORK_DISABLED is True
    assert ROOT_FILESYSTEM_READONLY is True
    assert DROP_CAPABILITIES == ("ALL",)
    assert NO_NEW_PRIVILEGES is True
    assert NON_ROOT_USER == "sandbox:sandbox"
