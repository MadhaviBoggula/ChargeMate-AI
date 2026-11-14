
import logging
from typing import Any, Callable

from langgraph.graph import END, START, StateGraph

from app.agents.shared.nodes import create_nodes
from app.agents.shared.state import GraphState
from app.agents.shared.tools import EmptyToolRegistry, ToolRegistry

logger = logging.getLogger("chargemate.agents")

GraphFactory = Callable[[], Any]

_graph_registry: dict[str, GraphFactory] = {}


def register_graph(role: str, factory: GraphFactory) -> None:
    """Register a role-specific graph factory (owner or driver)."""

    _graph_registry[role.lower()] = factory


def build_agent_graph(
    role: str,
    llm: Any | None = None,
    tool_registry: ToolRegistry | None = None,
    retriever: Callable[..., Any] | None = None,
    max_tool_rounds: int | None = None,
):
    """
    Compile a role workflow graph from the shared building blocks.

    Members 2 and 3 compose owner-specific and driver-specific workflows
    on top of these nodes; the role boundary and confirmation handling
    stay fixed here.
    """

    from app.core.config import settings
    from app.llm.client import get_openrouter_client

    nodes = create_nodes(
        llm=llm or get_openrouter_client(),
        tool_registry=tool_registry or EmptyToolRegistry(),
        retriever=retriever,
        max_tool_rounds=max_tool_rounds,
    )

    builder = StateGraph(GraphState)

    builder.add_node("check_pending_confirmation", nodes["check_pending_confirmation"])
    builder.add_node("route_request", nodes["route_request"])
    builder.add_node("invoke_tools", nodes["invoke_tools"])
    builder.add_node("rag_retrieval", nodes["rag_retrieval"])
    builder.add_node("generate_response", nodes["generate_response"])

    builder.add_edge(START, "check_pending_confirmation")

    def _after_confirmation(state: GraphState) -> str:
        if state.get("route") == "respond":
            return "generate_response"

        return "route_request"

    def _after_routing(state: GraphState) -> str:
        route = state.get("route", "general")

        if route in ("tool", "rag"):
            return route

        return "generate_response"

    builder.add_conditional_edges(
        "check_pending_confirmation",
        _after_confirmation,
        {
            "generate_response": "generate_response",
            "route_request": "route_request",
        },
    )

    builder.add_conditional_edges(
        "route_request",
        _after_routing,
        {
            "tool": "invoke_tools",
            "rag": "rag_retrieval",
            "generate_response": "generate_response",
        },
    )

    builder.add_edge("invoke_tools", "generate_response")
    builder.add_edge("rag_retrieval", "generate_response")
    builder.add_edge("generate_response", END)

    return builder.compile()


def _ensure_role_graphs_registered() -> None:
    if not _graph_registry:
        from app.agents.driver.graph import build_driver_graph
        from app.agents.owner.graph import build_owner_graph

        register_graph("owner", build_owner_graph)
        register_graph("driver", build_driver_graph)


def graph_for_role(role: str):
    """Return the compiled graph for a verified backend role."""

    _ensure_role_graphs_registered()

    factory = _graph_registry.get(role.lower())

    if factory is None:
        raise ValueError(f"No graph registered for role: {role}")

    return factory()


async def invoke_graph(
    role: str,
    user_id: str,
    conversation_id: str,
    message: str,
    history: list[dict[str, str]] | None = None,
    pending_confirmation: dict[str, Any] | None = None,
    confirmation_action: str | None = None,
) -> dict[str, Any]:
    """
    Role-based workflow selection and invocation.

    ``role`` MUST come from verified JWT context in the API layer and is
    never derived from prompt text or LLM output.
    """

    state: GraphState = {
        "user_id": str(user_id),
        "role": role,
        "conversation_id": str(conversation_id or ""),
        "current_request": message or "",
        "messages": list(history or []),
        "tool_results": [],
        "rag_context": [],
        "pending_confirmation": pending_confirmation,
        "confirmation_action": confirmation_action,
        "response": "",
    }

    graph = graph_for_role(role)
    result = await graph.ainvoke(state)

    return {
        "response": result.get("response", ""),
        "route": result.get("route", "general"),
        "tool_results": result.get("tool_results", []),
        "rag_context": result.get("rag_context", []),
        "pending_confirmation": result.get("pending_confirmation"),
    }
