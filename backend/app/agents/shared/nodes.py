"""Shared graph nodes and utilities (Member 4, lane A).

Building blocks Members 2 and 3 compose into owner/driver graphs:
- ``route_request``   : role-aware intent routing (general / tool / rag)
- ``invoke_tools``    : bounded MCP tool-call loop with MAX_TOOL_CALL_ROUNDS
- ``rag_retrieval``   : retrieval node wired to app.rag.retriever
- ``generate_response``: final grounded response generation
- ``load_history`` / ``save_messages``: persistence hooks calling Member 1's
  conversation services (wired when they land).
"""
import logging

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

from app.agents.shared.state import GraphState
from app.core.config import get_settings
from app.core.errors import UpstreamProviderError
from app.llm.client import get_chat_model

logger = logging.getLogger(__name__)
settings = get_settings()


async def route_request(state: GraphState) -> GraphState:
    """Role-aware routing between general chat, MCP tools, and RAG.

    Decision is made by the LLM using a strict routing prompt; role comes from
    trusted state only. Members 2/3 can override ``route_tools`` heuristics for
    domain-specific detection, but the role boundary is fixed here.
    """
    role = state.get("role", "driver")
    request = state.get("current_request") or ""
    route_prompt = (
        "Classify the user request into exactly one of: general, tool, rag.\n"
        "- tool: the request needs application data or an operation "
        f"(stations, chargers, sessions, revenue, availability, preferences, "
        f"favourites, bookings) that a {role} is permitted to perform.\n"
        "- rag: the request asks for domain knowledge, guidelines, or how-to "
        "information about EV charging.\n"
        "- general: anything else, including greetings and clarifications.\n"
        "Answer with the single word only."
    )
    try:
        result = await get_chat_model().ainvoke(
            [route_prompt, HumanMessage(content=request or "")]
        )
        label = str(result.content).strip().lower()
    except UpstreamProviderError:
        raise
    except Exception as exc:
        logger.warning("Routing LLM call failed, defaulting to general: %s", exc)
        label = "general"

    route = "general"
    for candidate in ("tool", "rag", "general"):
        if candidate in label:
            route = candidate
            break
    return {"route": route}


async def invoke_tools(state: GraphState) -> GraphState:
    """Bounded MCP tool-execution round.

    A real bound loop binds the role-scoped MCP tools to the chat model and
    runs at most ``MAX_TOOL_CALL_ROUNDS`` model<->tool exchanges. Until Member
    2/3 MCP servers are registered (URLs empty), this node returns a controlled
    result explaining that no tools are connected, so the graph degrades to a
    general response instead of crashing.
    """
    from app.mcp.client import get_mcp_client

    role = state.get("role", "driver")
    client = get_mcp_client()
    tools = await client.list_tools_for_role(role)
    if not tools:
        logger.info("No MCP tools registered for role=%s; skipping tool round", role)
        return {
            "route": "general",
            "tool_results": [
                {
                    "status": "unavailable",
                    "detail": f"No MCP tools are connected for role '{role}'.",
                }
            ],
        }
    # Placeholder for the bound loop; completed during MCP integration phase.
    return {"tool_results": [{"status": "not_implemented"}]}


async def rag_retrieval(state: GraphState) -> GraphState:
    """Retrieve knowledge chunks scoped to the user's role."""
    from app.rag.retriever import retrieve_for_role

    role = state.get("role", "driver")
    request = state.get("current_request") or ""
    chunks = await retrieve_for_role(role=role, query=request)
    return {"rag_context": chunks}


async def generate_response(state: GraphState) -> GraphState:
    """Grounded final response generation."""
    tool_results = state.get("tool_results") or []
    rag_context = state.get("rag_context") or []
    pending = state.get("pending_confirmation")

    parts: list[str] = []
    if rag_context:
        parts.append("Retrieved knowledge (cite only if relevant):\n")
        for chunk in rag_context:
            parts.append(f"- {chunk.get('content', '')}\n")
    if tool_results and tool_results[0].get("status") not in {"unavailable", "not_implemented"}:
        parts.append(f"Tool results: {tool_results}\n")
    if pending:
        parts.append(
            "A pending confirmation exists for action "
            f"'{pending.get('action')}'. Ask the user to confirm it in the "
            "application UI. Do not execute it yourself.\n"
        )

    messages: list = []
    if parts:
        messages.append(SystemMessage(content="Context:\n" + "\n".join(parts)))
    messages.extend(state.get("messages") or [])

    result = await get_chat_model().ainvoke(messages)
    return {"response": str(result.content)}


async def save_messages(state: GraphState) -> GraphState:
    """Persistence hook - Member 1's conversation services land here.

    Implemented as a no-op now so graphs compile and run before Member 1's
    persistence layer is merged.
    """
    return {}
