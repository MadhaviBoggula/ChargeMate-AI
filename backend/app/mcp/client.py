
import json
import logging
from contextlib import AsyncExitStack
from types import TracebackType
from typing import Any

from mcp import StdioServerParameters
from mcp.client.session import ClientSession
from mcp.client.sse import sse_client
from mcp.client.stdio import stdio_client
from mcp.client.streamable_http import streamablehttp_client

from app.agents.shared.tools import ToolContext
from app.core.config import settings

logger = logging.getLogger("chargemate.mcp")


class MCPConnectionError(Exception):
    """Raised when an MCP server cannot be connected to."""


class MCPToolError(Exception):
    """Raised when an MCP tool invocation fails structurally."""


def _is_http_url(server_url: str) -> bool:
    return server_url.startswith("http://") or server_url.startswith(
        "https://"
    )


def _split_stdio_command(server_url: str) -> StdioServerParameters:
    parts = server_url.split()

    if not parts:
        raise MCPConnectionError(
            "Empty MCP stdio command specification."
        )

    return StdioServerParameters(
        command=parts[0],
        args=parts[1:],
    )


class MCPServerConnection:
    """
    Manages one MCP server connection and keeps its session alive.

    Supports streamable HTTP, SSE, and stdio transports. Stdio is useful
    for running Members 2/3's servers locally during development; HTTP
    transports are the production path.
    """

    def __init__(self, name: str, server_url: str):
        self.name = name
        self.server_url = server_url
        self.session: ClientSession | None = None
        self._exit_stack = None

    @property
    def connected(self) -> bool:
        return self.session is not None

    async def connect(self) -> ClientSession:
        """Start the transport and initialize the session."""

        if self.connected:
            return self.session

        stack = AsyncExitStack()

        try:
            if _is_http_url(self.server_url):
                try:
                    transport = await stack.enter_async_context(
                        streamablehttp_client(self.server_url)
                    )
                except Exception:
                    logger.warning(
                        "Streamable HTTP connection to '%s' failed; "
                        "falling back to SSE",
                        self.name,
                    )
                    transport = await stack.enter_async_context(
                        sse_client(self.server_url)
                    )

                read_stream, write_stream = transport[0], transport[1]
            else:
                read_stream, write_stream = (
                    await stack.enter_async_context(
                        stdio_client(_split_stdio_command(self.server_url))
                    )
                )

            session = await stack.enter_async_context(
                ClientSession(read_stream, write_stream)
            )
            await session.initialize()

        except Exception as exc:
            await stack.aclose()

            raise MCPConnectionError(
                f"Could not connect to MCP server '{self.name}'."
            ) from exc

        self._exit_stack = stack
        self.session = session

        logger.info("Connected to MCP server '%s'", self.name)

        return session

    async def disconnect(self) -> None:
        if self._exit_stack is not None:
            await self._exit_stack.aclose()

        self._exit_stack = None
        self.session = None

        logger.info("Disconnected from MCP server '%s'", self.name)


def _result_text(result) -> str:
    parts = []

    for block in result.content:
        text = getattr(block, "text", None)

        if text is not None:
            parts.append(text)

    return "\n".join(parts)


class MCPToolRegistry:
    """
    Tool registry backed by a role's MCP server.

    Implements the shared ToolRegistry protocol so LangGraph nodes can
    list and invoke the role's tools without knowing about MCP.

    Identity contract: the authenticated user context is passed to every
    tool invocation as a reserved ``auth_context`` argument. The registry
    strips any model-supplied ``auth_context`` and injects the verified
    context itself, and hides the argument from the tool schema the LLM
    sees. MCP tools MUST derive the acting user from ``auth_context`` and
    never trust identity fields supplied in regular arguments.
    """

    RESERVED_CONTEXT_KEY = "auth_context"

    def __init__(self, role: str, server_url: str | None = None):
        self.role = role
        self.server_url = (
            server_url
            if server_url is not None
            else self._configured_server_url()
        )

    def _configured_server_url(self) -> str | None:
        if self.role == "owner":
            return settings.mcp_owner_server_url or None

        if self.role == "driver":
            return settings.mcp_driver_server_url or None

        return None

    @property
    def available(self) -> bool:
        return bool(self.server_url)

    async def _use_session(self, operation):
        """
        Run ``operation(session)`` over a fresh server connection.

        The connection is opened and closed inside the same async task,
        which anyio requires for its cancel scopes. Callers that issue
        several tool calls get one connection per call; a pooled
        long-lived client can replace this later once a single-task
        connection owner is in place.
        """

        if not self.available:
            raise MCPConnectionError(
                f"No MCP server is configured for role '{self.role}'."
            )

        connection = MCPServerConnection(
            name=f"{self.role}-mcp",
            server_url=self.server_url,
        )

        try:
            session = await connection.connect()
        except MCPConnectionError:
            await connection.disconnect()

            raise

        try:
            return await operation(session)
        finally:
            await connection.disconnect()

    def to_openai_schema(self, tool) -> dict[str, Any]:
        input_schema = dict(tool.inputSchema or {"type": "object", "properties": {}})

        properties = dict(input_schema.get("properties", {}))
        properties.pop(self.RESERVED_CONTEXT_KEY, None)
        input_schema["properties"] = properties

        required = [
            key
            for key in input_schema.get("required", [])
            if key != self.RESERVED_CONTEXT_KEY
        ]

        if required:
            input_schema["required"] = required
        else:
            input_schema.pop("required", None)

        return {
            "type": "function",
            "function": {
                "name": tool.name,
                "description": tool.description
                or f"MCP tool {tool.name}",
                "parameters": input_schema,
            },
        }

    async def list_tools(self, role: str) -> list[dict[str, Any]]:
        if not self.available:
            return []

        async def _list(session: ClientSession):
            try:
                listing = await session.list_tools()
            except Exception:
                logger.exception(
                    "Listing tools from MCP server '%s' failed", self.role
                )

                raise MCPConnectionError(
                    f"Could not list tools from MCP server '{self.role}'."
                )

            return [self.to_openai_schema(tool) for tool in listing.tools]

        return await self._use_session(_list)

    async def invoke_tool(
        self,
        role: str,
        name: str,
        arguments: dict[str, Any],
        context: ToolContext,
    ) -> dict[str, Any]:
        payload = dict(arguments or {})
        payload.pop(self.RESERVED_CONTEXT_KEY, None)
        payload[self.RESERVED_CONTEXT_KEY] = {
            "user_id": context.get("user_id"),
            "role": context.get("role"),
            "conversation_id": context.get("conversation_id"),
        }

        async def _call(session: ClientSession):
            try:
                result = await session.call_tool(name, payload)
            except Exception:
                logger.exception(
                    "MCP tool '%s' on server '%s' raised during transport",
                    name,
                    self.role,
                )

                return {
                    "status": "error",
                    "detail": (
                        f"Tool '{name}' could not be executed on the "
                        f"'{self.role}' server."
                    ),
                }

            if getattr(result, "isError", False):
                return {
                    "status": "error",
                    "detail": _result_text(result)
                    or f"Tool '{name}' reported an error.",
                }

            return self._parse_success(name, result)

        return await self._use_session(_call)

    def _parse_success(self, name: str, result) -> dict[str, Any]:
        text = _result_text(result)

        if not text:
            return {"status": "ok", "data": {}}

        try:
            data = json.loads(text)
        except (json.JSONDecodeError, TypeError):
            return {"status": "ok", "data": {"result": text}}

        if isinstance(data, dict) and "status" in data:
            return data

        return {"status": "ok", "data": data}

    async def aclose(self) -> None:
        """No persistent state to release; kept for lifecycle parity."""


_registries: dict[str, MCPToolRegistry | None] = {}


def get_default_tool_registry(role: str):
    """
    Return the role's default tool registry.

    Returns an MCP-backed registry when the role's server URL is
    configured, otherwise a registry that reports no tools so graphs
    degrade gracefully until Members 2/3 deploy their MCP servers.
    """

    from app.agents.shared.tools import EmptyToolRegistry

    role = role.lower()

    if role not in _registries:
        if role == "owner":
            url = settings.mcp_owner_server_url or None
        elif role == "driver":
            url = settings.mcp_driver_server_url or None
        else:
            url = None

        _registries[role] = (
            MCPToolRegistry(role=role, server_url=url)
            if url
            else EmptyToolRegistry()
        )

    registry = _registries[role]

    return registry if registry is not None else EmptyToolRegistry()


async def close_mcp_connections() -> None:
    """Release cached MCP registries (they hold no open connections)."""

    for registry in _registries.values():
        if isinstance(registry, MCPToolRegistry):
            await registry.aclose()

    _registries.clear()
