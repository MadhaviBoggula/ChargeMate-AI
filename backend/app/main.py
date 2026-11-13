"""ChargeMate AI application entry point.

Lifecycle: logging -> routers -> error handlers -> request-id middleware ->
startup/shutdown (DB engine, MCP shutdown).
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.core.config import get_settings
from app.core.logging import RequestIdMiddleware, setup_logging
from app.core.errors import register_error_handlers
from app.database.session import dispose_engine

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging(settings.log_level)
    yield
    dispose_engine()
    from app.mcp.client import shutdown_mcp

    await shutdown_mcp()


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.app_name,
        version="0.1.0",
        lifespan=lifespan,
        docs_url="/docs",
        openapi_url="/openapi.json",
    )

    from app.api import auth, bookings, chat, conversations, health

    app.include_router(health.router)
    app.include_router(auth.router, prefix=settings.api_v1_prefix)
    app.include_router(chat.router, prefix=settings.api_v1_prefix)
    app.include_router(conversations.router, prefix=settings.api_v1_prefix)
    app.include_router(bookings.router, prefix=settings.api_v1_prefix)

    register_error_handlers(app)
    app.add_middleware(RequestIdMiddleware)
    return app


app = create_app()
