
"""Evaluation runner (Member 4, lane E).

Runs each case through the real compiled graph with a scripted tool
registry and the live RAG retriever (when a DATABASE_URL is configured),
applies declarative checks, and produces a structured report.
"""
import logging
import time
from typing import Any

from app.agents.shared.runtime import build_agent_graph
from app.core.config import settings
from app.evaluation.cases import CASES, EvalCase
from app.evaluation.scripted import ScriptedToolRegistry

logger = logging.getLogger(__name__)


def _build_graph(role: str, registry: ScriptedToolRegistry):
    from app.rag.retriever import retrieve_for_role

    return build_agent_graph(
        role=role,
        tool_registry=registry,
        retriever=retrieve_for_role,
    )


def _run_one_turn(
    graph,
    registry: ScriptedToolRegistry,
    role: str,
    user_id: str,
    conversation_id: str,
    message: str,
    history: list[dict[str, str]],
    pending_confirmation: dict[str, Any] | None,
    confirmation_action: str | None,
) -> dict[str, Any]:
    state: dict[str, Any] = {
        "user_id": user_id,
        "role": role,
        "conversation_id": conversation_id,
        "current_request": message,
        "messages": list(history),
        "tool_results": [],
        "rag_context": [],
        "pending_confirmation": pending_confirmation,
        "confirmation_action": confirmation_action,
        "response": "",
    }

    return graph.invoke(state)


async def run_case(case: EvalCase) -> dict[str, Any]:
    """Run one evaluation case and return its structured result."""

    registry = ScriptedToolRegistry(case.role)
    graph = _build_graph(case.role, registry)

    user_id = f"eval-user-{case.role}"
    conversation_id = f"eval-conv-{case.id}"
    history: list[dict[str, str]] = []
    pending: dict[str, Any] | None = None

    result: dict[str, Any] = {
        "id": case.id,
        "category": case.category,
        "description": case.description,
        "role": case.role,
        "status": "passed",
        "failures": [],
        "route": None,
        "tools_called": [],
        "pending_confirmation": None,
        "rag_hits": 0,
        "response": "",
        "error": None,
    }

    try:
        for index, message in enumerate(case.turns):
            outcome = await graph.ainvoke(
                {
                    "user_id": user_id,
                    "role": case.role,
                    "conversation_id": conversation_id,
                    "current_request": message,
                    "messages": history,
                    "tool_results": [],
                    "rag_context": [],
                    "pending_confirmation": pending,
                    "confirmation_action": None,
                    "response": "",
                }
            )

            history = history + [
                {"role": "user", "content": message},
                {
                    "role": "assistant",
                    "content": outcome.get("response", ""),
                },
            ]
            pending = outcome.get("pending_confirmation")
            result["route"] = outcome.get("route", "general")
            result["response"] = outcome.get("response", "")
            result["rag_hits"] = len(outcome.get("rag_context") or [])

        extra = case.second_turn_extra

        if extra:
            carry_pending = (
                pending if extra.get("carry_pending") else None
            )

            outcome = await graph.ainvoke(
                {
                    "user_id": user_id,
                    "role": case.role,
                    "conversation_id": conversation_id,
                    "current_request": extra["message"],
                    "messages": history,
                    "tool_results": [],
                    "rag_context": [],
                    "pending_confirmation": carry_pending,
                    "confirmation_action": extra.get(
                        "confirmation_action"
                    ),
                    "response": "",
                }
            )

            result["route"] = outcome.get("route", "general")
            result["response"] = outcome.get("response", "")
            result["pending_confirmation"] = outcome.get(
                "pending_confirmation"
            )
        else:
            result["pending_confirmation"] = pending

        result["tools_called"] = registry.tool_names_called()
        _apply_checks(case, registry, result)
    except Exception as exc:
        logger.exception("Evaluation case '%s' raised", case.id)
        result["status"] = "error"
        result["error"] = f"{exc.__class__.__name__}: {exc}"
    else:
        result["status"] = (
            "passed" if not result["failures"] else "failed"
        )

    return result


def _apply_checks(
    case: EvalCase, registry: ScriptedToolRegistry, result: dict[str, Any]
) -> None:
    failures: list[str] = result["failures"]
    called = result["tools_called"]
    response = (result["response"] or "").lower()

    if case.expected_route and result["route"] != case.expected_route:
        failures.append(
            f"route: expected '{case.expected_route}', "
            f"got '{result['route']}'"
        )

    for tool in case.expected_tools:
        if tool not in called:
            failures.append(f"tool: expected call to '{tool}', not made")

    for tool in case.forbidden_tools:
        if tool in called:
            failures.append(f"tool: forbidden tool '{tool}' was called")

    if case.args_must_contain:
        matched = any(
            all(
                invocation["arguments"].get(key) == value
                for key, value in case.args_must_contain.items()
            )
            for invocation in registry.invocations
        )

        if not matched:
            failures.append(
                f"arguments: no call contained {case.args_must_contain}"
            )

    if case.rag_expected is True and result["rag_hits"] == 0:
        failures.append("rag: expected retrieved context, got none")

    if case.rag_expected is False and result["rag_hits"] > 0:
        failures.append("rag: expected no retrieved context, got hits")

    if case.pending_expected is True and not result["pending_confirmation"]:
        failures.append("pending: expected a pending confirmation")

    if case.pending_expected is False and result["pending_confirmation"]:
        failures.append("pending: pending confirmation still present")

    if case.confirm_attempted_must_be is False and any(
        invocation["tool"].startswith("confirm")
        for invocation in registry.invocations
    ):
        failures.append("pending: confirmation tool was executed")

    if case.response_must_include_any and not any(
        keyword in response
        for keyword in case.response_must_include_any
    ):
        failures.append(
            "response: none of the expected keywords "
            f"{case.response_must_include_any} found"
        )

    for keyword in case.response_must_not_include:
        if keyword in response:
            failures.append(
                f"response: forbidden phrase '{keyword}' present"
            )


async def run_evaluation(
    categories: list[str] | None = None,
) -> dict[str, Any]:
    """Run the full evaluation suite and return the report."""

    rag_available = bool(settings.database_url)

    selected = [
        case
        for case in CASES
        if categories is None or case.category in categories
    ]

    report: dict[str, Any] = {
        "started_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "rag_available": rag_available,
        "total": len(selected),
        "passed": 0,
        "failed": 0,
        "skipped": 0,
        "results": [],
    }

    for case in selected:
        if case.requires_rag and not rag_available:
            report["results"].append(
                {
                    "id": case.id,
                    "category": case.category,
                    "status": "skipped",
                    "reason": "DATABASE_URL not configured",
                }
            )
            report["skipped"] += 1
            continue

        started = time.perf_counter()
        outcome = await run_case(case)
        outcome["duration_s"] = round(time.perf_counter() - started, 2)
        report["results"].append(outcome)

        if outcome["status"] == "passed":
            report["passed"] += 1
        else:
            report["failed"] += 1

    return report


def format_report(report: dict[str, Any]) -> str:
    """Human-readable console summary."""

    lines = [
        "=" * 72,
        "ChargeMate AI - GenAI evaluation report",
        "=" * 72,
        f"RAG available: {report['rag_available']}",
        f"Total: {report['total']}  "
        f"Passed: {report['passed']}  Failed: {report['failed']}  "
        f"Skipped: {report['skipped']}",
        "-" * 72,
    ]

    for result in report["results"]:
        status = result["status"].upper()
        marker = {"PASSED": "PASS", "FAILED": "FAIL", "SKIPPED": "SKIP"}.get(
            status, status
        )

        lines.append(
            f"[{marker}] {result['id']} ({result['category']}) "
            f"{result.get('duration_s', '')}"
        )

        if result["status"] == "failed":
            for failure in result.get("failures", []):
                lines.append(f"       - {failure}")

            lines.append(f"       route={result.get('route')}")
            lines.append(f"       tools={result.get('tools_called')}")

            snippet = (result.get("response") or "")[:120].replace(
                "\n", " "
            )
            lines.append(f"       response={snippet!r}")

        elif result["status"] == "skipped":
            lines.append(f"       {result.get('reason')}")

    lines.append("=" * 72)

    return "\n".join(lines)
