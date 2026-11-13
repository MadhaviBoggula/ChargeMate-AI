"""Shared LangGraph runtime (Member 4, lane B).

- ``build_graph`` compiles a StateGraph from named nodes/edges; Members 2 and 3
  compose owner/driver graphs with these building blocks plus domain nodes.
- ``invoke_graph`` is the single entry the chat API uses, enforcing role-based
  workflow selection from trusted backend identity.
"""
from typing import Callable

from langgraph.graph import END, START, StateGraph

from app.agents.shared.nodes import (
    generate_response,
    invoke_tools,
    rag_retrieval,
    route_request,
)
from app.agents.shared.state import GraphState

# Registry of role-specific graphs; owner/driver modules register into this.
_graph_registry: dict[str, Callable[[], object]] = {}


def register_graph(role: str, factory: Callable[[], object]) -> None:
    _graph_registry[role.lower()] = factory


def build_graph(
    nodes: dict[str, Callable],
    edges: dict[str, str | list[str]],
    entry: str = "route_request",
):
    """Compile a StateGraph from node functions and static edges.

    ``edges`` maps source node -> destination node name or list of names.
    """
    builder = StateGraph(GraphState)
    for name, fn in nodes.items():
        builder.add_node(name, fn)

    builder.add_edge(START, entry)
    for src, dst in edges.items():
        for d in dst if isinstance(dst, list) else [dst]:
            if d == END:
                builder.add_edge(src, END)
            else:
                builder.add_edge(src, d)
    return builder.compile()


def build_default_graph():
    """Baseline graph used until Members 2/3 register domain workflows:
    route_request -> (tool | rag | general) -> generate_response -> save."""
    return build_graph(
        nodes={
            "route_request": route_request,
            "invoke_tools": invoke_tools,
            "rag_retrieval": rag_retrieval,
            "generate_response": generate_response,
            "save_messages": save_messages_placeholder,
        },
        edges={
            "route_request": ["invoke_tools", "rag_retrieval", "generate_response"],
            "invoke_tools": "generate_response",
            "rag_retrieval": "generate_response",
            "generate_response": "save_messages",
            "save_messages": END,
        },
    )


async def save_messages_placeholder(state: GraphState) -> GraphState:
    from app.agents.shared.nodes import save_messages

    return await save_messages(state)


def _graph_for_role(role: str):
    factory = _graph_registry.get(role.lower())
    graph = factory() if factory else build_default_graph()
    return graph


async def invoke_graph(
    role: str,
    user_id: str,
    conversation_id: str,
    message: str,
    history: list | None = None,
) -> dict:
    """Role-based workflow selection + invocation.

    ``role`` MUST come from verified JWT context in the API layer.
    """
    graph = _graph_for_role(role)
    state: GraphState = {
        "user_id": user_id,
        "role": role,
        "conversation_id": conversation_id,
        "messages": history or [],
        "current_request": message,
        "tool_results": [],
        "rag_context": [],
        "pending_confirmation": None,
        "response": "",
    }
    result = await graph.ainvoke(state)
    return {
        "response": result.get("response", ""),
        "route": result.get("route", "general"),
        "pending_confirmation": result.get("pending_confirmation"),
        "tool_results": result.get("tool_results", []),
    }
