
from typing import Any, Literal, TypedDict


class PendingConfirmation(TypedDict, total=False):
    """Metadata for an operation awaiting an explicit user action.

    ``tool`` and ``arguments`` describe the exact operation to execute when
    the user confirms. The graph never approves a pending action by itself;
    ``confirmation_action`` is injected by the backend from an explicit UI
    action and never comes from LLM output.
    """

    action: str
    proposal_id: str | None
    tool: str
    arguments: dict[str, Any]
    summary: dict[str, Any]


class GraphState(TypedDict, total=False):
    """
    Shared LangGraph state for owner and driver workflows.

    Trusted backend context (``user_id`` and ``role``) is set by the API
    layer from the verified JWT and never by the LLM.
    """

    user_id: str
    role: Literal["owner", "driver"]

    conversation_id: str
    current_request: str
    messages: list[dict[str, Any]]

    route: Literal["general", "tool", "rag", "respond"]
    tool_results: list[dict[str, Any]]
    rag_context: list[dict[str, Any]]

    pending_confirmation: PendingConfirmation | None
    confirmation_action: Literal["confirm", "reject"] | None

    response: str
