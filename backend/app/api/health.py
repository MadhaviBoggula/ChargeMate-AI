"""Health and readiness endpoints."""
from fastapi import APIRouter

from app.core.config import get_settings

router = APIRouter(tags=["health"])
settings = get_settings()


@router.get("/health")
async def health() -> dict:
    return {"status": "ok", "app": settings.app_name, "env": settings.app_env}


@router.get("/ready")
async def ready() -> dict:
    checks: dict[str, str] = {}
    try:
        from sqlalchemy import text

        from app.database.session import get_engine

        with get_engine().connect() as conn:
            conn.execute(text("SELECT 1"))
        checks["database"] = "ok"
    except Exception as exc:
        checks["database"] = f"error: {exc.__class__.__name__}"

    llm = "ok" if settings.openrouter_api_key else "not_configured"
    embeddings = settings.rag_sentence_transformers_model
    mcp_owner = bool(settings.mcp_owner_server_url)
    mcp_driver = bool(settings.mcp_driver_server_url)

    ready = all(v == "ok" for k, v in checks.items()) and llm == "ok"
    return {
        "status": "ready" if ready else "degraded",
        "checks": {
            **checks,
            "llm_provider": llm,
            "embedding_model": embeddings,
            "mcp_owner_registered": mcp_owner,
            "mcp_driver_registered": mcp_driver,
        },
    }
