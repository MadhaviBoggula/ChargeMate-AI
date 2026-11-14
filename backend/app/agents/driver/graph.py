
from typing import Any, Callable

from app.agents.shared.runtime import build_agent_graph, register_graph


def build_driver_graph(
    llm: Any | None = None,
    tool_registry: Any | None = None,
    retriever: Callable[..., Any] | None = None,
    max_tool_rounds: int | None = None,
):
    """
    Driver workflow graph.

    Framework, routing, and confirmation handling are Member 4's; Member 3
    plugs in the driver MCP tool registry and the booking subworkflow
    (prepare proposal -> explicit confirmation -> confirm). Booking
    confirmation pause/resume flows through GraphState.pending_confirmation
    and confirmation_action injected by the chat API.
    """

    return build_agent_graph(
        role="driver",
        llm=llm,
        tool_registry=tool_registry,
        retriever=retriever,
        max_tool_rounds=max_tool_rounds,
    )


register_graph("driver", build_driver_graph)
