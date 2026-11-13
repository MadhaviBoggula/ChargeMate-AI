"""MCP client and connection management (Member 4, lane C).

Registers the Owner MCP server (Member 2) and Driver MCP server (Member 3)
when their URLs are configured in settings. Until then, every method returns
gracefully-empty results so the LangGraph layer degrades instead of crashing.

Security invariants (task doc 6.C):
- The acting user's identity/role is injected here from trusted backend
  context - the LLM can never supply or override it.
- Tool exposure is role-scoped: owner tools never reach the driver workflow
  and vice versa.
- Provider/connection failures are normalized into structured outcomes.
"""
import logging
from dataclasses import dataclass, field

from app.core.config import get_settings
from app.core.errors import UpstreamProviderError

logger = logging.getLogger(__name__)
settings = get_settings()


@dataclass
class MCPToolResult:
    """Normalized MCP output for LangGraph consumption."""

    status: str  # "ok" | "error" | "unavailable"
    data: dict = field(default_factory=dict)
    error: str | None = None


@dataclass
class _ServerConnection:
    role: str
    url: str
    connected: bool = False
    tool_names: list[str] = field(default_factory=list)


class MCPClientManager:
    """Owns connections to both role MCP servers."""

    def __init__(self) -> None:
        self._connections: dict[str, _ServerConnection] = {}

    def _configured_url(self, role: str) -> str:
        return settings.mcp_url_for_role(role)

    async def _ensure_connection(self, role: str) -> _ServerConnection | None:
        url = self._configured_url(role)
        if not url:
            return None
        conn = self._connections.get(role)
        if conn and conn.connected and conn.url == url:
            return conn
        try:
            # Actual streamable-http session setup lands with the MCP
            # integration phase; structure is fixed now.
            from mcp.client.streamable_http import streamablehttp_client  # noqa: F401

            conn = _ServerConnection(role=role, url=url)
            self._connections[role] = conn
            conn.connected = False  # set True once session handshake succeeds
            logger.info("MCP server registered for role=%s url=%s", role, url)
            return conn
        except Exception as exc:
            logger.warning("MCP connection failed for role=%s: %s", role, exc)
            return None

    async def list_tools_for_role(self, role: str) -> list[str]:
        conn = await self._ensure_connection(role)
        if conn is None or not conn.connected:
            return []
        return conn.tool_names

    async def call_tool(
        self,
        role: str,
        tool_name: str,
        arguments: dict,
        user_id: str,
    ) -> MCPToolResult:
        """Execute a role-scoped tool with trusted user context.

        ``user_id`` comes from the verified JWT in the API layer and is passed
        to the MCP server as trusted execution context, never as an LLM-chosen
        argument.
        """
        conn = await self._ensure_connection(role)
        if conn is None or not conn.connected:
            return MCPToolResult(
                status="unavailable",
                error=f"MCP server for role '{role}' is not connected yet.",
            )
        try:
            # Session-based tool invocation lands with the MCP phase.
            return MCPToolResult(status="not_implemented")
        except Exception as exc:
            logger.exception("MCP tool execution failed")
            raise UpstreamProviderError(
                "Tool execution failed upstream.", details=None
            ) from exc


_manager: MCPClientManager | None = None


def get_mcp_client() -> MCPClientManager:
    global _manager
    if _manager is None:
        _manager = MCPClientManager()
    return _manager


async def shutdown_mcp() -> None:
    """Close connections on app shutdown."""
    global _manager
    _manager = None
