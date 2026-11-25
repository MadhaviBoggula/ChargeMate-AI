
class AppError(Exception):
    """Base class for expected application errors."""

    status_code = 500
    error_code = "app_error"

    def __init__(self, message: str, details: dict | None = None):
        self.message = message
        self.details = details or {}
        super().__init__(message)


class ValidationError(AppError):
    """Raised for invalid input or unsupported values."""

    status_code = 400
    error_code = "validation_error"


class UpstreamProviderError(AppError):
    """Raised when an external provider (LLM, embeddings) fails."""

    status_code = 502
    error_code = "upstream_provider_error"
