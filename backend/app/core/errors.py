"""Common API error conventions (Member 1's lane - scaffolded as shared contract).

Every domain error maps to a consistent structured payload:
``{"error": {"code": ..., "message": ..., "details": ...}}``.
"""
from typing import Any

from fastapi import Request, status
from fastapi.responses import JSONResponse


class AppError(Exception):
    """Base class for all controlled backend errors."""

    status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR
    code: str = "internal_error"

    def __init__(self, message: str, details: Any = None) -> None:
        self.message = message
        self.details = details
        super().__init__(message)


class ValidationError(AppError):
    status_code = status.HTTP_422_UNPROCESSABLE_ENTITY
    code = "validation_error"


class UnauthorizedError(AppError):
    status_code = status.HTTP_401_UNAUTHORIZED
    code = "unauthorized"


class InvalidTokenError(UnauthorizedError):
    code = "invalid_token"


class ForbiddenError(AppError):
    status_code = status.HTTP_403_FORBIDDEN
    code = "forbidden"


class NotFoundError(AppError):
    status_code = status.HTTP_404_NOT_FOUND
    code = "not_found"


class ConflictError(AppError):
    status_code = status.HTTP_409_CONFLICT
    code = "conflict"


class UpstreamProviderError(AppError):
    """Controlled failure for LLM/MCP/embedding provider issues.

    Never leaks secrets or internal stack traces to the client.
    """

    status_code = status.HTTP_502_BAD_GATEWAY
    code = "upstream_provider_error"


def error_response(exc: AppError, request_id: str | None = None) -> JSONResponse:
    body = {
        "error": {"code": exc.code, "message": exc.message, "details": exc.details}
    }
    headers = {"X-Request-ID": request_id} if request_id else None
    return JSONResponse(status_code=exc.status_code, content=body, headers=headers)


def register_error_handlers(app) -> None:
    """Install a consistent exception-handling layer."""

    @app.exception_handler(AppError)
    async def handle_app_error(request: Request, exc: AppError) -> JSONResponse:
        return error_response(exc, request.headers.get("X-Request-ID"))

    @app.exception_handler(Exception)
    async def handle_unexpected(request: Request, exc: Exception) -> JSONResponse:
        # Controlled 500: log internally, never expose stack traces.
        import logging

        logging.getLogger(__name__).exception("Unhandled exception")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": {
                    "code": "internal_error",
                    "message": "An unexpected error occurred.",
                    "details": None,
                }
            },
        )
