
import asyncio

from app.agents.shared.runtime import build_agent_graph

from tests.fakes import (
    FakeLLMClient,
    FakeToolRegistry,
    build_completion,
    build_initial_state,
    build_tool_call,
    llm_error,
)


def build_graph(
    chat_replies=None,
    registry=None,
    retriever=None,
    completions=None,
    completion_factory=None,
    chat_errors=None,
    **kwargs,
):
    llm = FakeLLMClient(
        chat_replies=chat_replies,
        completions=completions,
        completion_factory=completion_factory,
        chat_errors=chat_errors,
    )

    graph = build_agent_graph(
        role="owner",
        llm=llm,
        tool_registry=registry or FakeToolRegistry(),
        retriever=retriever,
        **kwargs,
    )

    return graph, llm


def run(graph, state):
    return asyncio.run(graph.ainvoke(state))


def test_general_route_skips_tools():
    registry = FakeToolRegistry(tools=["get_owner_stations"])
    graph, llm = build_graph(
        chat_replies=["general", "Hello! How can I help you?"],
        registry=registry,
    )

    result = run(graph, build_initial_state())

    assert result["route"] == "general"
    assert result["response"] == "Hello! How can I help you?"
    assert result["tool_results"] == []
    assert registry.invocations == []


def test_tool_route_executes_registered_tool():
    registry = FakeToolRegistry(tools=["get_owner_stations"])
    graph, llm = build_graph(
        chat_replies=["tool", "Here are your stations."],
        registry=registry,
        completions=[
            build_completion(
                tool_calls=[
                    build_tool_call(
                        "call_1",
                        "get_owner_stations",
                        {"limit": 5},
                    )
                ]
            ),
            build_completion(content="loop done"),
        ],
    )

    result = run(graph, build_initial_state())

    assert result["route"] == "tool"
    assert result["response"] == "Here are your stations."

    assert len(registry.invocations) == 1

    invocation = registry.invocations[0]

    assert invocation["name"] == "get_owner_stations"
    assert invocation["arguments"] == {"limit": 5}
    assert invocation["role"] == "owner"

    statuses = [entry["status"] for entry in result["tool_results"]]

    assert statuses == ["ok"]


def test_tool_rounds_are_bounded():
    registry = FakeToolRegistry(tools=["get_owner_stations"])
    graph, llm = build_graph(
        chat_replies=["tool", "Stopping here."],
        registry=registry,
        completion_factory=lambda: build_completion(
            tool_calls=[build_tool_call("call_n", "get_owner_stations", {})]
        ),
        max_tool_rounds=2,
    )

    result = run(graph, build_initial_state())

    assert len(registry.invocations) == 2
    assert len(llm.complete_calls) == 2

    notices = [
        entry
        for entry in result["tool_results"]
        if entry.get("status") == "notice"
    ]

    assert len(notices) == 1
    assert "Stopped after 2" in notices[0]["detail"]


def test_tool_route_without_tools_degrades_to_general():
    graph, llm = build_graph(
        chat_replies=["tool", "I can still help generally."],
        registry=FakeToolRegistry(),
    )

    result = run(graph, build_initial_state())

    assert result["route"] == "general"
    assert len(result["tool_results"]) == 1
    assert result["tool_results"][0]["status"] == "unavailable"
    assert result["response"] == "I can still help generally."


def test_invalid_tool_arguments_are_normalized():
    registry = FakeToolRegistry(tools=["get_owner_stations"])
    graph, llm = build_graph(
        chat_replies=["tool", "Could not process that."],
        registry=registry,
        completions=[
            build_completion(
                tool_calls=[
                    build_tool_call("call_bad", "get_owner_stations", "not-json")
                ]
            ),
            build_completion(content="loop done"),
        ],
    )

    result = run(graph, build_initial_state())

    assert registry.invocations == []
    assert result["tool_results"][0]["status"] == "error"
    assert result["tool_results"][0]["detail"] == "Invalid tool arguments."


def test_tool_failure_is_normalized_not_raised():
    registry = FakeToolRegistry(
        tools=["get_owner_stations"],
        error_tools={"get_owner_stations"},
    )
    graph, llm = build_graph(
        chat_replies=["tool", "Something went wrong."],
        registry=registry,
        completions=[
            build_completion(
                tool_calls=[build_tool_call("call_1", "get_owner_stations", {})]
            ),
            build_completion(content="loop done"),
        ],
    )

    result = run(graph, build_initial_state())

    assert result["tool_results"][0]["status"] == "error"
    assert "failed" in result["tool_results"][0]["detail"]
    assert result["response"] == "Something went wrong."


def test_rag_route_uses_retriever():
    async def retriever(role, query):
        return [{"content": "DC chargers need monthly checks.", "source": "doc1"}]

    graph, llm = build_graph(
        chat_replies=["rag", "Based on the knowledge base: monthly checks."],
        retriever=retriever,
    )

    result = run(graph, build_initial_state(current_request="How to maintain DC chargers?"))

    assert result["route"] == "rag"
    assert len(result["rag_context"]) == 1
    assert result["response"] == "Based on the knowledge base: monthly checks."


def test_rag_route_without_retriever_still_responds():
    graph, llm = build_graph(
        chat_replies=["rag", "I do not have that information."],
        retriever=None,
    )

    result = run(graph, build_initial_state())

    assert result["route"] == "rag"
    assert result["rag_context"] == []
    assert result["response"] == "I do not have that information."


def test_routing_llm_failure_defaults_to_general():
    registry = FakeToolRegistry(tools=["get_owner_stations"])
    graph, llm = build_graph(
        chat_replies=["Fallback answer."],
        registry=registry,
        chat_errors=[llm_error()],
    )

    result = run(graph, build_initial_state())

    assert result["route"] == "general"
    assert result["response"] == "Fallback answer."
    assert registry.invocations == []
