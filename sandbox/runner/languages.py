"""
Per-language compile and run command templates for the sandbox.
"""

from typing import Any, Dict, List, Optional


def get_language_config(language: str) -> Optional[Dict[str, Any]]:
    """Get configuration for a supported language."""

    configs: Dict[str, Dict[str, Any]] = {
        "python": {
            "name": "python",
            "image": "coding-mentor-python:latest",
            "fallback_image": "ai-screener-sandbox:latest",
            "filename": "main.py",
            "compile_command": None,
            "run_command": ["python3", "main.py"],
            "extensions": [".py"],
        },
        "python3": {
            "name": "python",
            "image": "coding-mentor-python:latest",
            "fallback_image": "ai-screener-sandbox:latest",
            "filename": "main.py",
            "compile_command": None,
            "run_command": ["python3", "main.py"],
            "extensions": [".py"],
        },
        "java": {
            "name": "java",
            "image": "coding-mentor-java:latest",
            "filename": "Main.java",
            "compile_command": ["javac", "Main.java"],
            "run_command": ["java", "Main"],
            "extensions": [".java"],
        },
        "cpp": {
            "name": "cpp",
            "image": "coding-mentor-cpp:latest",
            "filename": "main.cpp",
            "compile_command": ["g++", "-O2", "-std=c++17", "-o", "main", "main.cpp"],
            "run_command": ["./main"],
            "extensions": [".cpp", ".cc", ".cxx"],
        },
    }

    return configs.get(language.lower().strip())


def get_supported_languages() -> List[str]:
    """Get list of supported programming languages."""
    return ["python", "python3", "java", "cpp"]
