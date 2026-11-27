
import time
from contextlib import asynccontextmanager

from app.core.logger import setup_logging, get_logger

# ==========================================================
# 1. INITIALIZE LOGGING
# ==========================================================

setup_logging()

logger = get_logger(__name__)

logger.info("=" * 60)
logger.info("ChargeMate AI Backend initialization started")
logger.info("=" * 60)


# ==========================================================
# 2. IMPORT APPLICATION MODULES
# ==========================================================

try:
    logger.debug("[IMPORT] Importing FastAPI modules")

    from fastapi import FastAPI, HTTPException
    from fastapi.middleware.cors import CORSMiddleware
    from sqlalchemy import text

    logger.debug("[IMPORT] FastAPI modules imported")

    logger.debug("[IMPORT] Loading application settings")

    from app.core.config import settings

    logger.debug("[IMPORT] Application settings loaded")

    logger.debug("[IMPORT] Loading database engine")

    from app.database.session import engine

    logger.debug("[IMPORT] Database engine loaded")

    logger.debug("[IMPORT] Loading MCP client")

    from app.mcp.client import close_mcp_connections

    logger.debug("[IMPORT] MCP client loaded")

    logger.debug("[IMPORT] Loading logging middleware")

    from app.middleware.logging_middleware import LoggingMiddleware

    logger.debug("[IMPORT] Logging middleware loaded")

    # Import API routers

    logger.debug("[IMPORT] Loading authentication router")
    from app.api.routes.auth import router as auth_router

    logger.debug("[IMPORT] Loading bookings router")
    from app.api.routes.bookings import router as bookings_router

    logger.debug("[IMPORT] Loading chat router")
    from app.api.routes.chat import router as chat_router

    logger.debug("[IMPORT] Loading conversations router")
    from app.api.routes.conversations import router as conversations_router

    logger.debug("[IMPORT] Loading driver router")
    from app.api.routes.driver import router as driver_router

    logger.debug("[IMPORT] Loading owner router")
    from app.api.routes.owner import router as owner_router

    logger.debug("[IMPORT] Loading addresses router")
    from app.routers.addresses import router as addresses_router

    logger.debug("[IMPORT] Loading station router")
    from app.routers.station import router as station_router

    logger.info("[IMPORT] All application modules loaded successfully")

except Exception:
    logger.exception("[IMPORT FAILED] Application module import failed")
    raise


# ==========================================================
# 3. APPLICATION LIFESPAN
# ==========================================================

@asynccontextmanager
async def lifespan(app: FastAPI):

    start_time = time.perf_counter()

    logger.info("=" * 60)
    logger.info("[STARTUP] ChargeMate AI application starting")
    logger.info("[STARTUP] Application: %s", settings.app_name)
    logger.info("[STARTUP] Version: %s", settings.app_version)
    logger.info("[STARTUP] Debug mode: %s", settings.debug)
    logger.info("[STARTUP] API prefix: %s", settings.api_v1_prefix)

    # Check database connectivity during startup.
    # A failed check is logged but does not prevent startup.

    try:
        logger.info("[DATABASE] Checking database connectivity")

        database_start = time.perf_counter()

        with engine.connect() as connection:

            logger.debug("[DATABASE] Connection established")

            connection.execute(text("SELECT 1"))

            logger.debug("[DATABASE] Test query executed")

        database_duration = (
            time.perf_counter() - database_start
        )

        logger.info(
            "[DATABASE] Database connected successfully | Time: %.3fs",
            database_duration,
        )

    except Exception:

        logger.exception(
            "[DATABASE FAILED] Startup database connection check failed"
        )

        logger.warning(
            "[STARTUP] Application will start, "
            "but database operations may be unavailable"
        )

    startup_duration = time.perf_counter() - start_time

    logger.info(
        "[STARTUP] Application startup completed | Time: %.3fs",
        startup_duration,
    )

    logger.info("=" * 60)

    try:
        yield

    finally:

        # Application shutdown

        shutdown_start = time.perf_counter()

        logger.info("=" * 60)
        logger.info("[SHUTDOWN] ChargeMate AI shutting down")

        # Close MCP connections

        try:

            logger.info("[SHUTDOWN] Closing MCP connections")

            await close_mcp_connections()

            logger.info(
                "[SHUTDOWN] MCP connections closed successfully"
            )

        except Exception:

            logger.exception(
                "[SHUTDOWN FAILED] Error closing MCP connections"
            )

        # Dispose database engine

        try:

            logger.info("[SHUTDOWN] Disposing database engine")

            engine.dispose()

            logger.info(
                "[SHUTDOWN] Database engine disposed successfully"
            )

        except Exception:

            logger.exception(
                "[SHUTDOWN FAILED] Error disposing database engine"
            )

        logger.info(
            "[SHUTDOWN] Cleanup finished | Time: %.3fs",
            time.perf_counter() - shutdown_start,
        )

        logger.info("=" * 60)


# ==========================================================
# 4. CREATE FASTAPI APPLICATION
# ==========================================================

try:

    logger.info("[APP] Creating FastAPI application")

    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description="ChargeMate AI Backend API",
        debug=settings.debug,
        lifespan=lifespan,
    )

    logger.info("[APP] FastAPI application created successfully")

except Exception:

    logger.exception("[APP FAILED] FastAPI initialization failed")
    raise


# ==========================================================
# 5. REGISTER LOGGING MIDDLEWARE
# ==========================================================

logger.info("[MIDDLEWARE] Registering logging middleware")

app.add_middleware(LoggingMiddleware)

logger.info("[MIDDLEWARE] Logging middleware registered")


# ==========================================================
# 6. REGISTER CORS MIDDLEWARE
# ==========================================================

logger.info("[MIDDLEWARE] Configuring CORS middleware")

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

logger.info("[MIDDLEWARE] CORS middleware configured")


# ==========================================================
# 7. REGISTER API ROUTERS
# ==========================================================

try:

    logger.info("[ROUTERS] Registering API routers")

    # Authentication

    logger.debug("[ROUTER] Registering Authentication")

    app.include_router(
        auth_router,
        prefix=f"{settings.api_v1_prefix}/auth",
        tags=["Authentication"],
    )

    logger.info("[ROUTER] Authentication registered")

    # Conversations

    logger.debug("[ROUTER] Registering Conversations")

    app.include_router(
        conversations_router,
        prefix=f"{settings.api_v1_prefix}/conversations",
        tags=["Conversations"],
    )

    logger.info("[ROUTER] Conversations registered")

    # AI chat assistant

    logger.debug("[ROUTER] Registering AI Chat")

    app.include_router(
        chat_router,
        prefix=f"{settings.api_v1_prefix}/chat",
        tags=["Chat"],
    )

    logger.info("[ROUTER] AI Chat registered")

    # Charging stations

    logger.debug("[ROUTER] Registering Charging Stations")

    app.include_router(station_router)

    logger.info("[ROUTER] Charging Stations registered")

    # Addresses

    logger.debug("[ROUTER] Registering Addresses")

    app.include_router(addresses_router)

    logger.info("[ROUTER] Addresses registered")

    # Owner station and charger management

    logger.debug("[ROUTER] Registering Owner Management")

    app.include_router(
        owner_router,
        prefix=f"{settings.api_v1_prefix}/owner",
        tags=["Owner Station Management"],
    )

    logger.info("[ROUTER] Owner Management registered")

    # Driver vehicles and favorite stations

    logger.debug("[ROUTER] Registering Driver Management")

    app.include_router(
        driver_router,
        prefix=f"{settings.api_v1_prefix}/driver",
    )

    logger.info("[ROUTER] Driver Management registered")

    # Driver bookings

    logger.debug("[ROUTER] Registering Driver Bookings")

    app.include_router(
        bookings_router,
        prefix=f"{settings.api_v1_prefix}/bookings",
        tags=["Driver Bookings"],
    )

    logger.info("[ROUTER] Driver Bookings registered")

    logger.info("[ROUTERS] All API routers registered successfully")

except Exception:

    logger.exception("[ROUTER FAILED] API router registration failed")
    raise


# ==========================================================
# 8. HEALTH CHECK ENDPOINT
# ==========================================================

@app.get("/health", tags=["Health"])
def health_check():

    logger.debug("[HEALTH] Health check started")

    response = {
        "status": "healthy",
        "application": settings.app_name,
        "version": settings.app_version,
    }

    logger.info("[HEALTH] Health check successful")

    return response


# ==========================================================
# 9. DATABASE READINESS CHECK
# ==========================================================

@app.get("/ready", tags=["Health"])
def readiness_check():

    start_time = time.perf_counter()

    logger.info("[READY] Database readiness check started")

    try:

        logger.debug("[READY] Opening database connection")

        with engine.connect() as connection:

            logger.debug("[READY] Database connection established")

            logger.debug("[READY] Executing SELECT 1")

            connection.execute(text("SELECT 1"))

            logger.debug("[READY] Database query completed")

        duration = time.perf_counter() - start_time

        logger.info(
            "[READY] Database readiness check successful | Time: %.3fs",
            duration,
        )

        return {
            "status": "ready",
            "database": "connected",
        }

    except Exception:

        duration = time.perf_counter() - start_time

        logger.exception(
            "[READY FAILED] Database readiness check failed | Time: %.3fs",
            duration,
        )

        raise HTTPException(
            status_code=503,
            detail={
                "status": "not_ready",
                "database": "unavailable",
            },
        )


# ==========================================================
# 10. APPLICATION INITIALIZATION COMPLETED
# ==========================================================

logger.info("=" * 60)
logger.info("[APP] ChargeMate AI initialization completed")
logger.info("[APP] Total registered routes: %s", len(app.routes))
logger.info("[APP] Waiting for application startup")
logger.info("=" * 60)
