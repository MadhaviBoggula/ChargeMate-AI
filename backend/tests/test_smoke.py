"""Smoke tests for the ChargeMate AI foundation.

Live-provider tests are skipped unless their env credentials exist, so
``pytest`` runs green on a clean checkout.
"""
import pytest
from fastapi.testclient import TestClient

from app.main import create_app


@pytest.fixture
def client() -> TestClient:
    return TestClient(create_app())


def test_health(client: TestClient) -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_request_id_header(client: TestClient) -> None:
    response = client.get("/health")
    assert response.headers.get("X-Request-ID")


def test_ready_reports_component_status(client: TestClient) -> None:
    response = client.get("/ready")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] in {"ready", "degraded"}
    assert "database" in body["checks"]


def test_chat_requires_auth() -> None:
    """Chat must fail (not silently answer) until auth lands."""
    client = TestClient(create_app())
    response = client.post("/api/v1/chat", json={"message": "hi"})
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "unauthorized"


@pytest.mark.asyncio
async def test_mcp_graceful_when_unregistered() -> None:
    """MCP client degrades gracefully with empty server URLs."""
    from app.mcp.client import get_mcp_client

    manager = get_mcp_client()
    tools = await manager.list_tools_for_role("owner")
    assert tools == []
    result = await manager.call_tool(
        role="owner", tool_name="get_owner_stations", arguments={}, user_id="u1"
    )
    assert result.status == "unavailable"


@pytest.mark.skipif(
    not __import__("os").environ.get("OPENROUTER_API_KEY"),
    reason="OpenRouter credentials not configured",
)
@pytest.mark.asyncio
async def test_llm_reachable() -> None:
    from app.llm.client import get_chat_model

    result = await get_chat_model().ainvoke("Reply with exactly: PING")
    assert str(result.content)
