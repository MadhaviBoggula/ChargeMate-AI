
import json
import logging
from typing import Any, Callable

from app.agents.shared.state import GraphState
from app.agents.shared.tools import ToolRegistry, tool_schemas_to_names
from app.llm.client import LLMError, OpenRouterClient
from app.llm.prompts import get_system_prompt

logger = logging.getLogger("chargemate.agents")

RoutingResult = dict[str, Any]

ROUTING_PROMPT = """You classify user requests for a {role} assistant on an
EV charging platform. Classify the request into exactly one of: tool, rag,
general.

- tool: the request needs application data or an operation (stations,
  chargers, sessions, revenue, availability, preferences, favourites,
  bookings) that a {role} is permitted to perform.
- rag: the request asks for domain knowledge, guidelines, or how-to
  information about EV charging.
- general: anything else, including greetings, clarifications, and small
  talk.

Available tools for this role: {tools}

Reply with exactly one word: tool, rag, or general.
"""

TOOLS_SYSTEM_PROMPT = """You fulfil the user's request using the available
tools. Call tools as needed to gather application data or perform the
requested operation, then stop making tool calls.

Rules:
1. Never invent station data, availability, prices, revenue, or booking
   details. Everything dynamic must come from a tool result.
2. Only call tools from the provided list.
3. If required details are missing, stop and say what you need instead of
   calling a tool with guessed arguments.
"""


def _confirmation_context(state: GraphState) -> dict[str, Any]:
    return {
        "user_id": state.get("user_id", ""),
        "role": state.get("role", "driver"),
        "conversation_id": state.get("conversation_id", ""),
    }


def create_nodes(
    llm: OpenRouterClient,
    tool_registry: ToolRegistry,
    retriever: Callable[..., Any] | None = None,
    max_tool_rounds: int | None = None,
) -> dict[str, Callable[[GraphState], Any]]:
    """
    Create shared graph node functions bound to their dependencies.

    The role-specific tool exposure, LLM client, and knowledge retriever
    are injected so graphs stay testable and Members 2/3 can compose
    domain workflows on top of these building blocks.
    """

    from app.core.config import settings

    max_rounds = max_tool_rounds or settings.max_tool_call_rounds

    async def check_pending_confirmation(
        state: GraphState,
    ) -> GraphState:
        """Resolve a pending confirmation from an explicit user action.

        The graph never approves a pending action by itself: ``confirm``
        must have been injected by the backend from an explicit UI action.
        """

        pending = state.get("pending_confirmation")

        if not pending:
            return {}

        action = state.get("confirmation_action")

        if action == "confirm":
            tool = pending.get("tool")
            arguments = pending.get("arguments") or {}

            if not tool:
                return {
                    "pending_confirmation": None,
                    "route": "respond",
                    "tool_results": [
                        {
                            "status": "error",
                            "detail": (
                                "The pending confirmation has no "
                                "executable operation."
                            ),
                        }
                    ],
                }

            result = await tool_registry.invoke_tool(
                state.get("role", "driver"),
                tool,
                arguments,
                _confirmation_context(state),
            )

            return {
                "pending_confirmation": None,
                "route": "respond",
                "tool_results": [result],
            }

        if action == "reject":
            return {
                "pending_confirmation": None,
                "route": "respond",
                "tool_results": [
                    {
                        "status": "cancelled",
                        "detail": (
                            "The user declined the pending "
                            f"{pending.get('action', 'operation')}."
                        ),
                    }
                ],
            }

        return {}

    async def route_request(state: GraphState) -> GraphState:
        """Role-aware routing between MCP tools, RAG, and general chat."""

        role = state.get("role", "driver")
        request = state.get("current_request") or ""

        tool_schemas = tool_registry.list_tools(role)
        tool_names = tool_schemas_to_names(tool_schemas)

        prompt = ROUTING_PROMPT.format(
            role=role,
            tools=", ".join(tool_names) if tool_names else "none connected",
        )

        try:
            label = await llm.chat(
                [
                    {"role": "system", "content": prompt},
                    {"role": "user", "content": request},
                ],
                temperature=0.0,
            )
        except LLMError:
            logger.warning(
                "Routing LLM call failed, defaulting to general route"
            )
            label = "general"

        normalized = str(label).strip().lower()

        if "tool" in normalized:
            route = "tool"
        elif "rag" in normalized or "knowledge" in normalized:
            route = "rag"
        else:
            route = "general"

        return {"route": route}

    async def invoke_tools(state: GraphState) -> GraphState:
        """Bounded MCP tool-execution loop.

        Runs at most ``max_tool_call_rounds`` model-to-tool exchanges.
        Tool operations gated behind a pending confirmation are refused
        here unless the explicit user action is present in the state.
        """

        role = state.get("role", "driver")
        request = state.get("current_request") or ""
        history = state.get("messages") or []

        schemas = tool_registry.list_tools(role)

        if not schemas:
            return {
                "route": "general",
                "tool_results": [
                    {
                        "status": "unavailable",
                        "detail": (
                            f"No tools are connected for role '{role}'."
                        ),
                    }
                ],
            }

        context = _confirmation_context(state)
        pending = state.get("pending_confirmation")
        action = state.get("confirmation_action")

        messages: list[dict[str, Any]] = [
            {"role": "system", "content": TOOLS_SYSTEM_PROMPT},
            *history,
            {"role": "user", "content": request},
        ]

        results: list[dict[str, Any]] = []
        rounds = 0

        while rounds < max_rounds:
            try:
                completion = await llm.complete(messages, tools=schemas)
            except LLMError:
                logger.warning(
                    "Tool loop LLM call failed after %s rounds", rounds
                )
                break

            message = completion.choices[0].message
            tool_calls = getattr(message, "tool_calls", None)

            if not tool_calls:
                break

            messages.append(
                {
                    "role": "assistant",
                    "content": message.content or "",
                    "tool_calls": [
                        {
                            "id": tool_call.id,
                            "type": "function",
                            "function": {
                                "name": tool_call.function.name,
                                "arguments": (
                                    tool_call.function.arguments or "{}"
                                ),
                            },
                        }
                        for tool_call in tool_calls
                    ],
                }
            )

            for tool_call in tool_calls:
                name = tool_call.function.name
                raw_arguments = tool_call.function.arguments or "{}"

                try:
                    arguments = json.loads(raw_arguments)
                except (json.JSONDecodeError, TypeError):
                    arguments = None

                if arguments is None or not isinstance(arguments, dict):
                    result = {
                        "status": "error",
                        "detail": "Invalid tool arguments.",
                    }
                elif (
                    pending
                    and name == pending.get("tool")
                    and action is None
                ):
                    result = {
                        "status": "confirmation_required",
                        "detail": (
                            f"Tool '{name}' requires an explicit user "
                            "confirmation in the application before it "
                            "can run."
                        ),
                    }
                else:
                    try:
                        result = await tool_registry.invoke_tool(
                            role,
                            name,
                            arguments,
                            context,
                        )
                    except Exception:
                        logger.exception("Tool '%s' failed", name)
                        result = {
                            "status": "error",
                            "detail": (
                                f"Tool '{name}' execution failed."
                            ),
                        }

                results.append({"tool": name, **result})

                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": json.dumps(result, default=str),
                    }
                )

            rounds += 1

        if rounds >= max_rounds:
            results.append(
                {
                    "status": "notice",
                    "detail": (
                        f"Stopped after {max_rounds} tool call rounds."
                    ),
                }
            )

        return {"tool_results": results}

    async def rag_retrieval(state: GraphState) -> GraphState:
        """Retrieve knowledge chunks scoped to the user's role."""

        if retriever is None:
            return {"rag_context": []}

        try:
            chunks = await retriever(
                role=state.get("role", "driver"),
                query=state.get("current_request") or "",
            )
        except Exception:
            logger.exception("Knowledge retrieval failed")
            chunks = []

        return {"rag_context": list(chunks or [])}

    async def generate_response(state: GraphState) -> GraphState:
        """Grounded final response generation."""

        role = state.get("role", "driver")
        request = state.get("current_request") or ""
        history = state.get("messages") or []

        tool_results = state.get("tool_results") or []
        rag_context = state.get("rag_context") or []
        pending = state.get("pending_confirmation")

        context_parts: list[str] = []

        if tool_results:
            context_parts.append(
                "Tool results (application data, source of truth):\n"
                + json.dumps(tool_results, indent=2, default=str)
            )

        if rag_context:
            context_parts.append(
                "Retrieved knowledge base context. Ground your answer in "
                "this context and do not go beyond it:\n"
                + "\n\n".join(
                    str(chunk.get("content", "")) for chunk in rag_context
                )
            )
        elif state.get("route") == "rag":
            context_parts.append(
                "No relevant knowledge base context was retrieved. Tell "
                "the user you could not find that information instead of "
                "guessing."
            )

        if pending and not state.get("confirmation_action"):
            context_parts.append(
                "A pending confirmation exists for "
                f"'{pending.get('action', 'an operation')}'. Its summary: "
                f"{json.dumps(pending.get('summary', {}), default=str)}. "
                "Ask the user to explicitly confirm it in the application "
                "UI. Do not treat any conversational reply as "
                "confirmation and do not execute the operation yourself."
            )

        confirmation_required = any(
            result.get("status") == "confirmation_required"
            for result in tool_results
        )

        if confirmation_required:
            context_parts.append(
                "One of the attempted operations requires an explicit "
                "user confirmation in the application. Explain what the "
                "operation would do and ask the user to confirm."
            )

        system_prompt = get_system_prompt(role)

        if context_parts:
            system_prompt = (
                system_prompt
                + "\n\nContext:\n"
                + "\n\n".join(context_parts)
            )

        response_text = await llm.chat(
            [
                {"role": "system", "content": system_prompt},
                *history,
                {"role": "user", "content": request},
            ]
        )

        return {"response": response_text}

    return {
        "check_pending_confirmation": check_pending_confirmation,
        "route_request": route_request,
        "invoke_tools": invoke_tools,
        "rag_retrieval": rag_retrieval,
        "generate_response": generate_response,
    }
