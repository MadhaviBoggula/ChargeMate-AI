
import json
import logging
from contextlib import asynccontextmanager
from datetime import datetime, timezone

from fastapi import FastAPI, HTTPException
from sqlalchemy import text

from app.api.routes.auth import router as auth_router
from app.api.routes.chat import router as chat_router
from app.api.routes.conversations import (
    router as conversations_router,
)
from app.core.config import settings
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
