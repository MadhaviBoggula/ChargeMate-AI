"""Common LangGraph graph state (Member 4, lane A).

Agreed state contract (task doc 4.A):
- ``user_id`` / ``role`` come from verified JWT backend context - NEVER from
  prompt text or LLM output.
- ``pending_confirmation`` carries metadata for operations awaiting an explicit
  UI action (especially booking confirmation). The graph never approves a
  pending action by itself.
"""
from typing import Annotated, Any, Literal, TypedDict

from langchain_core.messages import AnyMessage
from langgraph.graph.message import add_messages


class PendingConfirmation(TypedDict, total=False):
    action: str
    proposal_id: str
    summary: dict[str, Any]


class GraphState(TypedDict, total=False):
    # Trusted backend context (set by the API layer from JWT, never by the LLM)
    user_id: str
    role: Literal["owner", "driver"]

    # Conversation
    conversation_id: str
    messages: Annotated[list[AnyMessage], add_messages]
    current_request: str

    # Execution path
    route: Literal["general", "tool", "rag"]
    tool_results: list[dict[str, Any]]
    rag_context: list[dict[str, Any]]

    # Confirmation workflow
    pending_confirmation: PendingConfirmation | None

    # Output
    response: str
