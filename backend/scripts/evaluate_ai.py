
"""GenAI evaluation CLI (Member 4, lane E).

Runs the behavioral evaluation suite against the real OpenRouter model
and the live RAG collection (when DATABASE_URL is configured), using a
scripted tool registry so no MCP server needs to be deployed.

Usage (from backend/):
    .venv\\Scripts\\python.exe scripts\\evaluate_ai.py
    .venv\\Scripts\\python.exe scripts\\evaluate_ai.py --category routing
    .venv\\Scripts\\python.exe scripts\\evaluate_ai.py --json out\\eval_report.json
"""
import argparse
import asyncio
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.evaluation.runner import format_report, run_evaluation  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run the GenAI behavioral evaluation suite"
    )
    parser.add_argument(
        "--category",
        action="append",
        choices=[
            "routing",
            "tool_selection",
            "rag",
            "refusal",
            "followup",
            "confirmation",
            "security",
        ],
        help="Limit to one or more categories (repeatable)",
    )
    parser.add_argument(
        "--json",
        type=Path,
        help="Also write the full report as JSON to this path",
    )
    args = parser.parse_args()

    report = asyncio.run(run_evaluation(categories=args.category))

    print(format_report(report))

    if args.json:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(
            json.dumps(report, indent=2, default=str), encoding="utf-8"
        )
        print(f"JSON report written to {args.json}")

    return 1 if report["failed"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
