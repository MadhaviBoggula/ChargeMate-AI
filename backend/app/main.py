import json
import logging
import time
from contextlib import asynccontextmanager
from datetime import datetime, timezone

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.api.routes.auth import router as auth_router
from app.api.routes.bookings import router as bookings_router
from app.api.routes.chat import router as chat_router
from app.api.routes.conversations import router as conversations_router
from app.api.routes.driver import router as driver_router
from app.api.routes.owner import router as owner_router
from app.core.config import settings
from app.database.session import engine
from app.mcp.client import close_mcp_connections
from app.routers.addresses import router as addresses_router
from app.routers.station import router as station_router


class JSONFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        for field in (
            "http_method",
            "http_path",
            "status_code",
            "duration_ms",
        ):
            if hasattr(record, field):
                log_data[field] = getattr(record, field)

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


configure_logging()
logger = logging.getLogger("chargemate")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("ChargeMate AI application starting")
    yield
    logger.info("ChargeMate AI application shutting down")
    await close_mcp_connections()
    engine.dispose()


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="ChargeMate AI Backend API",
    debug=settings.debug,
    lifespan=lifespan,
)


@app.middleware("http")
async def request_logging_middleware(
    request: Request,
    call_next,
):
    start_time = time.perf_counter()

    method = request.method
    path = request.url.path

    try:
        response = await call_next(request)

        duration_ms = round(
            (time.perf_counter() - start_time) * 1000,
            2,
        )

        logger.info(
            "HTTP request completed",
            extra={
                "http_method": method,
                "http_path": path,
                "status_code": response.status_code,
                "duration_ms": duration_ms,
            },
        )

        return response

    except Exception:
        duration_ms = round(
            (time.perf_counter() - start_time) * 1000,
            2,
        )

        logger.exception(
            "HTTP request failed",
            extra={
                "http_method": method,
                "http_path": path,
                "duration_ms": duration_ms,
            },
        )
        raise


app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Authentication
app.include_router(
    auth_router,
    prefix=f"{settings.api_v1_prefix}/auth",
    tags=["Authentication"],
)

# Conversations
app.include_router(
    conversations_router,
    prefix=f"{settings.api_v1_prefix}/conversations",
    tags=["Conversations"],
)

# AI chat assistant
app.include_router(
    chat_router,
    prefix=f"{settings.api_v1_prefix}/chat",
    tags=["Chat"],
)

# Charging stations (router already defines its API prefix)
app.include_router(station_router)

# Addresses (router already defines its API prefix)
app.include_router(addresses_router)

# Owner station and charger management
app.include_router(
    owner_router,
    prefix=f"{settings.api_v1_prefix}/owner",
    tags=["Owner Station Management"],
)

# Driver vehicles and favorite stations
app.include_router(
    driver_router,
    prefix=f"{settings.api_v1_prefix}/driver",
)

# Driver bookings
app.include_router(
    bookings_router,
    prefix=f"{settings.api_v1_prefix}/bookings",
    tags=["Driver Bookings"],
)


@app.get("/health", tags=["Health"])
def health_check():
    return {
        "status": "healthy",
        "application": settings.app_name,
        "version": settings.app_version,
    }


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
