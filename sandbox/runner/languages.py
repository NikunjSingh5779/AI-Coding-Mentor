"""
Per-language compile and run command templates for the sandbox.
"""

from typing import Dict, Any, Optional


def get_language_config(language: str) -> Optional[Dict[str, Any]]:
    """Get configuration for a supported language."""

    configs = {
        "python": {
            "name": "python",
            "filename": "main.py",
            "compile_command": None,  # No compilation needed
            "run_command": ["python", "main.py"],
            "timeout": 30,
            "extensions": [".py"]
        },

        "java": {
            "name": "java",
            "filename": "Main.java",
            "compile_command": ["javac", "Main.java"],
            "run_command": ["java", "Main"],
            "timeout": 30,
            "extensions": [".java"]
        },

        "cpp": {
            "name": "cpp",
            "filename": "main.cpp",
            "compile_command": ["g++", "-o", "main", "main.cpp", "-std=c++17"],
            "run_command": ["./main"],
            "timeout": 30,
            "extensions": [".cpp", ".cc", ".cxx"]
        },

        "c": {
            "name": "cpp",  # Uses same image as C++
            "filename": "main.c",
            "compile_command": ["gcc", "-o", "main", "main.c", "-std=c99"],
            "run_command": ["./main"],
            "timeout": 30,
            "extensions": [".c"]
        }
    }

    return configs.get(language.lower())


def get_supported_languages() -> list[str]:
    """Get list of supported programming languages."""
    return ["python", "java", "cpp", "c"]


def detect_language_from_code(code: str) -> str:
    """Simple heuristic to detect language from code content."""

    # Check for obvious markers
    if "public class" in code or "public static void main" in code:
        return "java"

    if "#include" in code and ("int main(" in code or "void main(" in code):
        if ".hpp" in code or "std::" in code or "namespace" in code:
            return "cpp"
        else:
            return "c"

    if "def " in code or "import " in code or "print(" in code:
        return "python"

    # Default fallback
    return "python"