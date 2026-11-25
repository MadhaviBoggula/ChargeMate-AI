
"""Evaluation harness tests (Member 4, lane E).

Offline tests of the evaluation machinery itself: the scripted tool
registry, the proposal->pending-confirmation contract, check logic, and
end-to-end case execution with a scripted fake LLM. Live model runs are
done separately via scripts/evaluate_ai.py.
"""
import pytest

from app.evaluation.cases import CASES
from app.evaluation.runner import _apply_checks, format_report, run_case
from app.evaluation.scripted import (
    DRIVER_TOOLS,
    OWNER_TOOLS,
    ScriptedToolRegistry,
)

from tests.fakes import (
    FakeLLMClient,
    build_completion,
    build_tool_call,
)


def _patched_build_graph(monkeypatch, llm: FakeLLMClient):
    """Point the runner's graph builder at a scripted fake LLM."""

    from app.agents.shared.runtime import build_agent_graph
    from app.rag.retriever import retrieve_for_role

    def factory(role, registry):
        return build_agent_graph(
            role=role,
            llm=llm,
            tool_registry=registry,
            retriever=retrieve_for_role,
        )

    monkeypatch.setattr("app.evaluation.runner._build_graph", factory)


# --- ScriptedToolRegistry ---


async def test_registry_exposes_only_role_tools():
    owner_registry = ScriptedToolRegistry("owner")
    driver_registry = ScriptedToolRegistry("driver")

    owner_names = {
        schema["function"]["name"]
        for schema in await owner_registry.list_tools("owner")
    }
    driver_names = {
        schema["function"]["name"]
        for schema in await driver_registry.list_tools("driver")
    }

    assert owner_names == set(OWNER_TOOLS)
    assert driver_names == set(DRIVER_TOOLS)

    # Role-exclusive tools must not cross over (a few generic names like
    # get_station_details exist on both sides by design)
    owner_only = owner_names - driver_names
    driver_only = driver_names - owner_names

    assert {"get_owner_stations", "get_station_revenue"} <= owner_only
    assert {
        "search_stations",
        "prepare_booking",
        "confirm_booking",
        "cancel_booking",
    } <= driver_only


async def test_registry_records_and_scripts_invocations():
    registry = ScriptedToolRegistry("owner")

    result = await registry.invoke_tool(
        "owner",
        "get_station_revenue",
        {"station_id": "st-1"},
        {"user_id": "u1", "role": "owner"},
    )

    assert result["data"]["revenue"] == 1832.4
    assert registry.invocations[0]["tool"] == "get_station_revenue"
    assert registry.invocations[0]["context"]["user_id"] == "u1"


async def test_registry_rejects_unknown_and_invalid_calls():
    registry = ScriptedToolRegistry("driver")

    unknown = await registry.invoke_tool(
        "driver", "get_station_analytics", {}, {}
    )
    assert unknown["status"] == "error"

    with pytest.raises(ValueError):
        await registry.invoke_tool("driver", "get_station_details", {}, {})


async def test_registry_relays_confirmation_request():
    registry = ScriptedToolRegistry("driver")

    result = await registry.invoke_tool(
        "driver",
        "prepare_booking",
        {"station_id": "st-1", "start_at": "tomorrow"},
        {},
    )

    assert result["confirmation_request"]["tool"] == "confirm_booking"


# --- Proposal contract in invoke_tools ---


def _scripted_llm_for_tool_call(tool_name: str, arguments: dict):
    return FakeLLMClient(
        chat_replies=["tool", "Please confirm this in the app."],
        completions=[
            build_completion(
                tool_calls=[build_tool_call("call-1", tool_name, arguments)]
            ),
            build_completion(content="done"),
        ],
    )


async def test_tool_result_proposal_sets_pending_confirmation(monkeypatch):
    from app.agents.shared.nodes import create_nodes
    from app.evaluation.scripted import ScriptedToolRegistry

    llm = _scripted_llm_for_tool_call(
        "prepare_booking",
        {"station_id": "st-1", "start_at": "2026-11-15T10:00:00Z"},
    )
    registry = ScriptedToolRegistry("driver")
    nodes = create_nodes(llm, registry, retriever=None)

    state = {
        "user_id": "u1",
        "role": "driver",
        "conversation_id": "c1",
        "current_request": "Book a slot",
        "messages": [],
        "tool_results": [],
        "rag_context": [],
        "pending_confirmation": None,
        "confirmation_action": None,
        "response": "",
    }

    outcome = await nodes["invoke_tools"](state)

    pending = outcome["pending_confirmation"]

    assert pending["tool"] == "confirm_booking"
    assert pending["arguments"]["proposal_id"] == "prop-1"
    assert pending["action"]


async def test_pending_not_overwritten_when_one_exists(monkeypatch):
    from app.agents.shared.nodes import create_nodes
    from app.evaluation.scripted import ScriptedToolRegistry

    llm = _scripted_llm_for_tool_call(
        "prepare_booking",
        {"station_id": "st-1", "start_at": "2026-11-15T10:00:00Z"},
    )
    registry = ScriptedToolRegistry("driver")
    nodes = create_nodes(llm, registry, retriever=None)

    existing = {"tool": "confirm_booking", "arguments": {"proposal_id": "x"}}

    state = {
        "user_id": "u1",
        "role": "driver",
        "conversation_id": "c1",
        "current_request": "Book another",
        "messages": [],
        "tool_results": [],
        "rag_context": [],
        "pending_confirmation": existing,
        "confirmation_action": None,
        "response": "",
    }

    outcome = await nodes["invoke_tools"](state)

    # The node must not emit a new proposal; LangGraph's state merge
    # keeps the existing pending_confirmation untouched.
    assert "pending_confirmation" not in outcome


# --- Check logic ---


def _result(**overrides):
    base = {
        "id": "x",
        "category": "test",
        "status": "passed",
        "failures": [],
        "route": "general",
        "tools_called": [],
        "pending_confirmation": None,
        "rag_hits": 0,
        "response": "",
    }
    base.update(overrides)
    return base


def test_check_route_and_tools():
    case = CASES[0]  # expects tool route + analytics call

    good = _result(route="tool", tools_called=["get_station_analytics"])
    _apply_checks(case, None, good)
    assert good["failures"] == []

    bad = _result(route="general", tools_called=[])
    _apply_checks(case, None, bad)
    assert len(bad["failures"]) == 2


def test_check_forbidden_tools():
    case = next(c for c in CASES if c.id == "security-role-confusion")

    result = _result(tools_called=["get_station_analytics"])
    _apply_checks(case, None, result)

    assert any("forbidden" in failure for failure in result["failures"])


def test_check_args_must_contain():
    case = next(c for c in CASES if c.id == "tool-owner-revenue-args")

    class _Registry:
        invocations = [
            {"tool": "get_station_revenue", "arguments": {"station_id": "st-9"}},
            {"tool": "get_station_revenue", "arguments": {"station_id": "st-1"}},
        ]

    result = _result(route="tool")
    _apply_checks(case, _Registry(), result)
    assert result["failures"] == []

    class _BadRegistry:
        invocations = [
            {"tool": "get_station_revenue", "arguments": {"station_id": "st-9"}},
        ]

    result = _result(route="tool")
    _apply_checks(case, _BadRegistry(), result)
    assert any("arguments" in failure for failure in result["failures"])


def test_check_response_keywords_and_pending():
    case = next(c for c in CASES if c.id == "confirm-proposal-created")

    result = _result(
        pending_confirmation={"tool": "confirm_booking"},
        response="Please confirm this in the app.",
    )
    _apply_checks(case, None, result)
    assert result["failures"] == []

    result = _result(response="Booking done!")
    _apply_checks(case, None, result)
    assert len(result["failures"]) == 2


# --- End-to-end case execution with the fake LLM ---


async def test_run_case_booking_flow_creates_pending(monkeypatch):
    case = next(c for c in CASES if c.id == "confirm-proposal-created")
    llm = _scripted_llm_for_tool_call(
        "prepare_booking",
        {"station_id": "st-1", "start_at": "2026-11-15T10:00:00Z"},
    )
    _patched_build_graph(monkeypatch, llm)

    result = await run_case(case)

    assert result["status"] == "passed", result["failures"]
    assert result["pending_confirmation"]["tool"] == "confirm_booking"
    assert result["tools_called"] == ["prepare_booking"]


async def test_run_case_reject_cancels_pending(monkeypatch):
    case = next(c for c in CASES if c.id == "confirm-reject")

    # Turn 1: route tool, call prepare_booking
    llm = FakeLLMClient(
        chat_replies=["tool", "Please confirm in the app.", "Cancelled."],
        completions=[
            build_completion(
                tool_calls=[
                    build_tool_call(
                        "call-1",
                        "prepare_booking",
                        {"station_id": "st-1", "start_at": "tomorrow"},
                    )
                ]
            )
        ],
    )
    _patched_build_graph(monkeypatch, llm)

    result = await run_case(case)

    assert result["status"] == "passed", result["failures"]
    assert result["pending_confirmation"] is None


async def test_run_case_bypass_attempt_does_not_execute(monkeypatch):
    case = next(c for c in CASES if c.id == "confirm-bypass-rejected")

    llm = FakeLLMClient(
        chat_replies=[
            "tool",
            "Please confirm in the app.",
            "tool",
            "Confirm in the app; chat cannot approve this.",
        ],
        completions=[
            # Turn 1: prepare_booking, then a same-loop confirm attempt
            build_completion(
                tool_calls=[
                    build_tool_call(
                        "call-1",
                        "prepare_booking",
                        {"station_id": "st-1", "start_at": "tomorrow"},
                    )
                ]
            ),
            build_completion(
                tool_calls=[
                    build_tool_call(
                        "call-2", "confirm_booking", {"proposal_id": "prop-1"}
                    )
                ]
            ),
            build_completion(content="done"),
            # Turn 2: another confirm attempt after a conversational "yes"
            build_completion(
                tool_calls=[
                    build_tool_call(
                        "call-3", "confirm_booking", {"proposal_id": "prop-1"}
                    )
                ]
            ),
            build_completion(content="done"),
        ],
    )
    _patched_build_graph(monkeypatch, llm)

    result = await run_case(case)

    assert result["status"] == "passed", result["failures"]
    assert result["tools_called"] == ["prepare_booking"]
    assert result["pending_confirmation"] is not None


async def test_run_case_reports_unexpected_behavior(monkeypatch):
    case = next(c for c in CASES if c.id == "route-owner-general")
    # Route to 'rag' although general expected -> deterministic failure
    llm = FakeLLMClient(chat_replies=["rag"])
    _patched_build_graph(monkeypatch, llm)

    result = await run_case(case)

    assert result["status"] == "failed"
    assert any(
        failure.startswith("route:") for failure in result["failures"]
    )


def test_format_report_renders_failures():
    report = {
        "rag_available": True,
        "total": 2,
        "passed": 1,
        "failed": 1,
        "skipped": 0,
        "results": [
            {
                "id": "ok-case",
                "category": "routing",
                "status": "passed",
                "duration_s": 1.0,
            },
            {
                "id": "bad-case",
                "category": "routing",
                "status": "failed",
                "failures": ["route: expected 'rag', got 'tool'"],
                "route": "tool",
                "tools_called": ["search_stations"],
                "response": "nope",
                "duration_s": 2.0,
            },
        ],
    }

    text = format_report(report)

    assert "[FAIL] bad-case" in text
    assert "route: expected 'rag', got 'tool'" in text
    assert "Passed: 1  Failed: 1" in text


def test_case_catalog_is_wellformed():
    ids = [case.id for case in CASES]

    assert len(ids) == len(set(ids))
    assert all(case.turns for case in CASES)
    assert all(
        case.category
        in {
            "routing",
            "tool_selection",
            "rag",
            "refusal",
            "followup",
            "confirmation",
            "security",
        }
        for case in CASES
    )
