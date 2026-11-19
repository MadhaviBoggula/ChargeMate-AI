
import asyncio
import json
import os
import sys

from groq import AsyncGroq
from openai import AsyncOpenAI
from anthropic import AsyncAnthropic
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from app.config import settings


INSTRUCTIONS = (
    "You are ChargeMate AI, an assistant for electric vehicle "
    "charging station owners. Use MCP tools to answer questions "
    "about the owner's stations and chargers. "
    "Never invent database information."
)

ALLOWED_TOOLS = {
    "list_my_stations",
    "get_station_details",
    "list_my_chargers",
}


def get_provider():
    provider = settings.ai_provider.lower()

    if provider == "groq":
        if not settings.groq_api_key:
            raise ValueError("GROQ_API_KEY is missing")
        return (
            AsyncGroq(api_key=settings.groq_api_key),
            settings.groq_model,
            provider,
        )

    if provider == "openai":
        if not settings.openai_api_key:
            raise ValueError("OPENAI_API_KEY is missing")
        return (
            AsyncOpenAI(api_key=settings.openai_api_key),
            settings.openai_model,
            provider,
        )

    if provider == "anthropic":
        if not settings.anthropic_api_key:
            raise ValueError("ANTHROPIC_API_KEY is missing")
        return (
            AsyncAnthropic(api_key=settings.anthropic_api_key),
            settings.anthropic_model,
            provider,
        )

    raise ValueError(f"Unsupported AI provider: {provider}")


async def execute_mcp_tool(session, name, arguments):
    if name not in ALLOWED_TOOLS:
        return "Error: MCP tool is not allowed"

    try:
        result = await session.call_tool(
            name,
            arguments=arguments,
        )

        parts = [
            item.text
            for item in result.content
            if hasattr(item, "text")
        ]

        result_text = "\n".join(parts)

        if not result_text:
            result_text = json.dumps(
                getattr(result, "structuredContent", {}) or {},
                default=str,
            )

        if result.isError:
            return "MCP tool execution failed: " + result_text

        return result_text

    except Exception as exc:
        return f"MCP tool error: {exc}"


async def chat_openai_compatible(
    client, model, messages, tools, session
):
    # Used by both Groq and OpenAI.
    for _ in range(10):
        response = await client.chat.completions.create(
            model=model,
            messages=messages,
            tools=tools if tools else None,
        )

        choice = response.choices[0]
        assistant_message = choice.message

        messages.append(
            assistant_message.model_dump(exclude_none=True)
        )

        calls = assistant_message.tool_calls or []

        if not calls:
            return assistant_message.content or ""

        for call in calls:
            print(f"\nExecuting MCP tool: {call.function.name}")

            try:
                arguments = json.loads(
                    call.function.arguments or "{}"
                )
                if not isinstance(arguments, dict):
                    raise ValueError("Expected JSON object")

                result = await execute_mcp_tool(
                    session,
                    call.function.name,
                    arguments,
                )
            except (ValueError, json.JSONDecodeError) as exc:
                result = f"Invalid tool arguments: {exc}"

            messages.append({
                "role": "tool",
                "tool_call_id": call.id,
                "content": result,
            })

    return "Stopped: too many consecutive tool calls."


async def chat_anthropic(
    client, model, messages, tools, session
):
    for _ in range(10):
        response = await client.messages.create(
            model=model,
            max_tokens=2048,
            system=INSTRUCTIONS,
            messages=messages,
            tools=tools,
        )

        assistant_blocks = [
            block.model_dump(exclude_none=True)
            for block in response.content
        ]

        messages.append({
            "role": "assistant",
            "content": assistant_blocks,
        })

        tool_uses = [
            block for block in response.content
            if block.type == "tool_use"
        ]

        if not tool_uses:
            return "\n".join(
                block.text
                for block in response.content
                if block.type == "text"
            )

        tool_results = []

        for call in tool_uses:
            print(f"\nExecuting MCP tool: {call.name}")

            result = await execute_mcp_tool(
                session,
                call.name,
                call.input,
            )

            tool_results.append({
                "type": "tool_result",
                "tool_use_id": call.id,
                "content": result,
            })

        messages.append({
            "role": "user",
            "content": tool_results,
        })

    return "Stopped: too many consecutive tool calls."


async def main():
    client, model, provider = get_provider()

    print(f"\nAI Provider: {provider.upper()}")
    print(f"AI Model: {model}")

    server_params = StdioServerParameters(
        command=sys.executable,
        args=["-m", "app.mcp.owner_server"],
        env=os.environ.copy(),
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            print("\nConnected to ChargeMate AI Owner MCP Server!")

            discovered = await session.list_tools()

            available_tools = [
                tool for tool in discovered.tools
                if tool.name in ALLOWED_TOOLS
            ]

            print("\nAvailable Owner MCP Tools:")
            for tool in available_tools:
                print("-", tool.name)

            if not available_tools:
                print("No allowed MCP tools found.")
                return

            if provider == "anthropic":
                tools = [
                    {
                        "name": tool.name,
                        "description": tool.description or "",
                        "input_schema": tool.inputSchema,
                    }
                    for tool in available_tools
                ]
                messages = []
            else:
                tools = [
                    {
                        "type": "function",
                        "function": {
                            "name": tool.name,
                            "description": tool.description or "",
                            "parameters": tool.inputSchema,
                        },
                    }
                    for tool in available_tools
                ]
                messages = [
                    {
                        "role": "system",
                        "content": INSTRUCTIONS,
                    }
                ]

            print("\nChargeMate AI Owner Assistant is ready!")
            print("Type 'exit' to stop.\n")

            while True:
                question = input("Owner: ").strip()

                if question.lower() in ("exit", "quit"):
                    print("Exiting ChargeMate AI...")
                    break

                if not question:
                    continue

                messages.append({
                    "role": "user",
                    "content": question,
                })

                try:
                    if provider == "anthropic":
                        answer = await chat_anthropic(
                            client, model, messages, tools, session
                        )
                    else:
                        answer = await chat_openai_compatible(
                            client, model, messages, tools, session
                        )

                    print("\nChargeMate AI:", answer, "\n")

                except Exception as exc:
                    # Avoid retaining an incomplete tool-call sequence.
                    messages = (
                        [] if provider == "anthropic"
                        else [{
                            "role": "system",
                            "content": INSTRUCTIONS,
                        }]
                    )

                    print(
                        f"\n{provider.upper()} request failed: "
                        f"{type(exc).__name__}: {exc}\n"
                    )


if __name__ == "__main__":
    asyncio.run(main())
