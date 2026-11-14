
from typing import Any, Callable

from app.agents.shared.runtime import build_agent_graph, register_graph


def build_owner_graph(
    llm: Any | None = None,
    tool_registry: Any | None = None,
    retriever: Callable[..., Any] | None = None,
    max_tool_rounds: int | None = None,
):
    """
    Owner workflow graph.

    Framework and routing are Member 4's; Member 2 plugs in the owner
    MCP tool registry and may compose additional domain nodes on top of
    the shared building blocks.
    """

    from app.mcp.client import get_default_tool_registry

    return build_agent_graph(
        role="owner",
        llm=llm,
        tool_registry=tool_registry or get_default_tool_registry("owner"),
        retriever=retriever,
        max_tool_rounds=max_tool_rounds,
    )


register_graph("owner", build_owner_graph)
