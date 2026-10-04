"""
Core error definitions and WebSocket/REST error mapping.
"""



class AppError(Exception):
    """Base application error with status code and error type."""

    def __init__(
        self, message: str, status_code: int = 500, error_type: str = "internal_error"
    ):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.error_type = error_type


class ValidationError(AppError):
    """Invalid input data."""

    def __init__(self, message: str):
        super().__init__(message, 400, "validation_error")


class NotFoundError(AppError):
    """Resource not found."""

    def __init__(self, message: str = "Resource not found"):
        super().__init__(message, 404, "not_found")


class ConflictError(AppError):
    """Resource conflict (e.g., duplicate session)."""

    def __init__(self, message: str):
        super().__init__(message, 409, "conflict")


class RateLimitError(AppError):
    """Rate limit exceeded."""

    def __init__(self, message: str = "Rate limit exceeded"):
        super().__init__(message, 429, "rate_limit_exceeded")


class SandboxError(AppError):
    """Sandbox execution error."""

    def __init__(self, message: str):
        super().__init__(message, 503, "sandbox_error")


class LLMError(AppError):
    """LLM service error."""

    def __init__(self, message: str):
        super().__init__(message, 503, "llm_error")
