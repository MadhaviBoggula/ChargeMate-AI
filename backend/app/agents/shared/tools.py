
import logging
from typing import Any, Protocol

logger = logging.getLogger("chargemate.tools")

ToolContext = dict[str, Any]


def normalize_tool_result(
    result: Any,
) -> dict[str, Any]:
    """Normalize any tool outcome into a consistent result mapping."""

    if isinstance(result, dict) and "status" in result:
        normalized = dict(result)
        normalized.setdefault("status", "error")
        return normalized

    if isinstance(result, dict):
        return {"status": "ok", "data": result}

    return {"status": "ok", "data": {"result": result}}


class ToolRegistry(Protocol):
    """Interface the MCP integration layer implements per role."""

    async def list_tools(self, role: str) -> list[dict[str, Any]]:
        """Return OpenAI-style tool schemas exposed to the given role."""

    async def invoke_tool(
        self,
        role: str,
        name: str,
        arguments: dict[str, Any],
        context: ToolContext,
    ) -> dict[str, Any]:
        """Execute a tool and return a normalized result."""


class EmptyToolRegistry:
    """Registry used before MCP servers are connected.

    Exposes no tools so graphs degrade gracefully to general responses
    instead of failing.
    """

    async def list_tools(self, role: str) -> list[dict[str, Any]]:
        return []

    async def invoke_tool(
        self,
        role: str,
        name: str,
        arguments: dict[str, Any],
        context: ToolContext,
    ) -> dict[str, Any]:
        return {
            "status": "error",
            "detail": f"Tool '{name}' is not available for role '{role}'.",
        }


def tool_schemas_to_names(schemas: list[dict[str, Any]]) -> list[str]:
    names = []

    for schema in schemas:
        function = schema.get("function", {})
        name = function.get("name")

        if name:
            names.append(name)

    return names
