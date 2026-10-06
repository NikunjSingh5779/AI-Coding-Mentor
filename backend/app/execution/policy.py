"""Execution limits and supported runtime policy."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ExecutionPolicy:
    timeout_seconds: int = 30
    max_timeout_seconds: int = 60
    memory_bytes: int = 256 * 1024 * 1024
    cpu_limit: float = 0.5
    pids_limit: int = 64
    max_output_bytes: int = 1_048_576
    max_code_bytes: int = 250_000


LANGUAGE_IMAGES = {
    "python": "coding-mentor-python:latest",
    "javascript": "coding-mentor-javascript:latest",
    "cpp": "coding-mentor-cpp:latest",
    "c": "coding-mentor-cpp:latest",
    "java": "coding-mentor-java:latest",
}


LANGUAGE_COMMANDS = {
    "python": ("main.py", "python /workspace/main.py"),
    "javascript": ("main.js", "node /workspace/main.js"),
    "cpp": ("main.cpp", "mkdir -p /tmp/work && cp /workspace/main.cpp /tmp/work/main.cpp && g++ -std=c++17 -O0 -pipe /tmp/work/main.cpp -o /tmp/work/main && /tmp/work/main"),
    "c": ("main.c", "mkdir -p /tmp/work && cp /workspace/main.c /tmp/work/main.c && gcc -std=c11 -O0 -pipe /tmp/work/main.c -o /tmp/work/main && /tmp/work/main"),
    "java": ("Main.java", "mkdir -p /tmp/work && cp /workspace/Main.java /tmp/work/Main.java && javac -d /tmp/work /tmp/work/Main.java && java -cp /tmp/work Main"),
}
