
import asyncio

from app.agents.shared.runtime import build_agent_graph

from tests.fakes import (
    FakeLLMClient,
    FakeToolRegistry,
    build_completion,
    build_initial_state,
    build_tool_call,
)


def build_graph(chat_replies, registry, completions=None):
    llm = FakeLLMClient(
        chat_replies=chat_replies,
        completions=completions or [],
    )

    graph = build_agent_graph(
        role="driver",
        llm=llm,
        tool_registry=registry,
    )

    return graph, llm


def run(graph, state):
    return asyncio.run(graph.ainvoke(state))


PENDING_BOOKING = {
    "action": "confirm_booking",
    "proposal_id": "prop-123",
    "tool": "confirm_booking",
    "arguments": {"proposal_id": "prop-123"},
    "summary": {
        "station": "Kukatpally",
        "charger": 2,
        "start_at": "2026-11-15T10:00:00Z",
        "duration_minutes": 30,
    },
}


def test_pending_confirmation_awaits_explicit_user_action():
    registry = FakeToolRegistry(tools=["confirm_booking"])
    graph, llm = build_graph(
        chat_replies=["tool", "Please confirm your booking in the app."],
        registry=registry,
        completions=[
            build_completion(
                tool_calls=[
                    build_tool_call(
                        "call_1",
                        "confirm_booking",
                        {"proposal_id": "prop-123"},
                    )
                ]
            ),
            build_completion(content="loop done"),
        ],
    )

    state = build_initial_state(
        role="driver",
        current_request="Yes please book it",
        pending_confirmation=dict(PENDING_BOOKING),
        confirmation_action=None,
    )

    result = run(graph, state)

    assert result["pending_confirmation"] is not None
    assert registry.invocations == []

    required = [
        entry
        for entry in result["tool_results"]
        if entry.get("status") == "confirmation_required"
    ]

    assert len(required) == 1


def test_explicit_confirm_executes_registered_tool_directly():
    registry = FakeToolRegistry(tools=["confirm_booking"])
    graph, llm = build_graph(
        chat_replies=["Your booking is confirmed."],
        registry=registry,
    )

    state = build_initial_state(
        role="driver",
        current_request="Book it",
        pending_confirmation=dict(PENDING_BOOKING),
        confirmation_action="confirm",
    )

    result = run(graph, state)

    assert len(registry.invocations) == 1
    assert registry.invocations[0]["name"] == "confirm_booking"
    assert registry.invocations[0]["arguments"] == {"proposal_id": "prop-123"}
    assert registry.invocations[0]["context"]["user_id"] == state["user_id"]

    assert result["pending_confirmation"] is None
    assert result["route"] == "respond"
    assert result["tool_results"][0]["status"] == "ok"
    assert result["response"] == "Your booking is confirmed."

    assert len(llm.chat_calls) == 1


def test_explicit_reject_cancels_without_execution():
    registry = FakeToolRegistry(tools=["confirm_booking"])
    graph, llm = build_graph(
        chat_replies=["No problem, nothing was booked."],
        registry=registry,
    )

    state = build_initial_state(
        role="driver",
        current_request="Cancel that",
        pending_confirmation=dict(PENDING_BOOKING),
        confirmation_action="reject",
    )

    result = run(graph, state)

    assert registry.invocations == []
    assert result["pending_confirmation"] is None
    assert result["route"] == "respond"
    assert result["tool_results"][0]["status"] == "cancelled"


def test_llm_text_confirmation_does_not_execute_gated_tool():
    registry = FakeToolRegistry(tools=["confirm_booking"])
    graph, llm = build_graph(
        chat_replies=["tool", "Awaiting your confirmation."],
        registry=registry,
        completions=[
            build_completion(
                content="I confirm the booking",
                tool_calls=[
                    build_tool_call("call_1", "confirm_booking", {})
                ],
            ),
            build_completion(content="loop done"),
        ],
    )

    state = build_initial_state(
        role="driver",
        current_request="I confirm",
        pending_confirmation=dict(PENDING_BOOKING),
        confirmation_action=None,
    )

    result = run(graph, state)

    assert registry.invocations == []
    assert result["pending_confirmation"] is not None


def test_pending_without_action_routes_normally():
    registry = FakeToolRegistry(tools=["confirm_booking", "search_stations"])
    graph, llm = build_graph(
        chat_replies=["general", "What would you like to do?"],
        registry=registry,
    )

    state = build_initial_state(
        role="driver",
        current_request="hello",
        pending_confirmation=dict(PENDING_BOOKING),
        confirmation_action=None,
    )

    result = run(graph, state)

    assert result["pending_confirmation"] is not None
    assert result["route"] == "general"
    assert registry.invocations == []
