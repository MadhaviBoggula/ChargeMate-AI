

import json
import logging
import time
import uuid
from contextlib import asynccontextmanager
from datetime import datetime, timezone

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.api.routes.auth import router as auth_router
from app.api.routes.bookings import router as bookings_router
from app.api.routes.chat import router as chat_router
from app.api.routes.conversations import (
    router as conversations_router,
)
from app.api.routes.driver import router as driver_router
from app.api.routes.owner import router as owner_router
from app.api.routes.stations import router as stations_router
from app.core.config import settings
from app.core.errors import AppError
from app.database.session import engine
from app.mcp.client import close_mcp_connections

# Structured JSON logging
class JSONFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        http = getattr(record, "http", None)

        if isinstance(http, dict):
            log_data["http"] = http

        if record.exc_info:
            log_data["exception"] = self.formatException(
                record.exc_info
            )

        return json.dumps(log_data)


def configure_logging() -> None:
    handler = logging.StreamHandler()
    handler.setFormatter(JSONFormatter())

    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.addHandler(handler)
    root_logger.setLevel(
        logging.DEBUG if settings.debug else logging.INFO
    )

    # Request logging is emitted by the application middleware below, so
    # uvicorn's plain access log would only duplicate it.
    logging.getLogger("uvicorn.access").disabled = True


configure_logging()
logger = logging.getLogger("chargemate")


# Application lifecycle
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("ChargeMate AI application starting")

    yield

    logger.info("ChargeMate AI application shutting down")

    await close_mcp_connections()
    engine.dispose()


# FastAPI application
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="ChargeMate AI Backend API",
    debug=settings.debug,
    lifespan=lifespan,
)


# Allow local frontends (Next.js and Vite) to call the API
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Request-ID"],
)


# Probes for OpenAI-compatible endpoints are not part of this API.
_SUPPRESSED_REQUEST_LOG_PATHS = ("/v1/models",)


def _should_log_request(path: str) -> bool:
    return not any(
        path == suppressed or path.startswith(f"{suppressed}/")
        for suppressed in _SUPPRESSED_REQUEST_LOG_PATHS
    )


def _request_log_fields(
    request: Request,
    status_code: int,
    duration_ms: float,
) -> dict:
    route = request.scope.get("route")
    action = getattr(route, "name", None)

    if action is None:
        endpoint = request.scope.get("endpoint")
        action = getattr(endpoint, "__name__", None)

    return {
        "request_id": getattr(request.state, "request_id", None),
        "method": request.method,
        "path": request.url.path,
        "query": request.url.query or None,
        "status_code": status_code,
        "duration_ms": duration_ms,
        "client_ip": request.client.host if request.client else None,
        "user_id": getattr(request.state, "user_id", None),
        "role": getattr(request.state, "role", None),
        "action": action or "unmatched",
    }


@app.middleware("http")
async def request_id_middleware(request: Request, call_next):
    """Attach a correlation id and log the completed request."""

    request_id = request.headers.get("X-Request-ID") or uuid.uuid4().hex
    request.state.request_id = request_id
    started = time.perf_counter()

    try:
        response = await call_next(request)
    except Exception:
        duration_ms = round((time.perf_counter() - started) * 1000, 2)

        if _should_log_request(request.url.path):
            logger.exception(
                "%s %s -> 500 (%.2fms)",
                request.method,
                request.url.path,
                duration_ms,
                extra={
                    "http": _request_log_fields(request, 500, duration_ms)
                },
            )

        raise

    duration_ms = round((time.perf_counter() - started) * 1000, 2)
    response.headers["X-Request-ID"] = request_id

    if _should_log_request(request.url.path):
        logger.info(
            "%s %s -> %s (%.2fms)",
            request.method,
            request.url.path,
            response.status_code,
            duration_ms,
            extra={
                "http": _request_log_fields(
                    request,
                    response.status_code,
                    duration_ms,
                )
            },
        )

    return response


# Authentication API routes
app.include_router(
    auth_router,
    prefix=f"{settings.api_v1_prefix}/auth",
    tags=["Authentication"],
)


# Conversation persistence API routes
app.include_router(
    conversations_router,
    prefix=f"{settings.api_v1_prefix}/conversations",
    tags=["Conversations"],
)


# Conversational assistant API routes
app.include_router(
    chat_router,
    prefix=f"{settings.api_v1_prefix}/chat",
    tags=["Chat"],
)


# Public charging station discovery
app.include_router(
    stations_router,
    prefix=f"{settings.api_v1_prefix}/stations",
    tags=["Stations"],
)


# Owner network management, revenue, and analytics
app.include_router(
    owner_router,
    prefix=f"{settings.api_v1_prefix}/owner",
    tags=["Owner"],
)


# Driver vehicles, preferences, favourites, and compatibility
app.include_router(
    driver_router,
    prefix=f"{settings.api_v1_prefix}/driver",
    tags=["Driver"],
)


# Driver booking lifecycle
app.include_router(
    bookings_router,
    prefix=f"{settings.api_v1_prefix}/bookings",
    tags=["Bookings"],
)


@app.exception_handler(AppError)
async def app_error_handler(
    request: Request,
    exc: AppError,
) -> JSONResponse:
    """Render expected service-layer errors as JSON responses."""

    content = {
        "detail": exc.message,
        "error": exc.error_code,
        "request_id": getattr(request.state, "request_id", None),
    }

    if exc.details:
        content["details"] = exc.details

    return JSONResponse(
        status_code=exc.status_code,
        content=content,
    )


@app.exception_handler(StarletteHTTPException)
async def http_error_handler(
    request: Request,
    exc: StarletteHTTPException,
) -> JSONResponse:
    """Render HTTP errors with a consistent envelope."""

    errors = {
        400: "bad_request",
        401: "unauthorized",
        403: "forbidden",
        404: "not_found",
        405: "method_not_allowed",
        409: "conflict",
        422: "validation_error",
        429: "rate_limited",
        503: "service_unavailable",
    }

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "detail": exc.detail,
            "error": errors.get(exc.status_code, "http_error"),
            "request_id": getattr(request.state, "request_id", None),
        },
        headers=getattr(exc, "headers", None),
    )


# Liveness check
@app.get("/health", tags=["Health"])
def health_check():
    return {
        "status": "healthy",
        "application": settings.app_name,
        "version": settings.app_version,
    }


# Readiness check
@app.get("/ready", tags=["Health"])
def readiness_check():
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))

        return {
            "status": "ready",
            "database": "connected",
        }

    except Exception:
        logger.exception("Database readiness check failed")

        raise HTTPException(
            status_code=503,
            detail={
                "status": "not_ready",
                "database": "unavailable",
            },
        )
    