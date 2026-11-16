
import asyncio
import json
import os
import sys

from openai import AsyncOpenAI, RateLimitError
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from app.config import settings

async def safe_openai_request(client, **kwargs):
    try:
        return await client.responses.create(**kwargs)

    except RateLimitError:
        print("\nOpenAI API quota exceeded.")
        print("Please check your API billing and available credits.")
        return None

async def main():

    # 1. Initialize OpenAI
    openai_client = AsyncOpenAI(
        api_key=settings.openai_api_key
    )

    # 2. Start Owner MCP server
    server_params = StdioServerParameters(
        command=sys.executable,
        args=["-m", "app.mcp.owner_server"],
        env=os.environ.copy(),
    )

    # 3. Connect MCP client to server
    async with stdio_client(server_params) as (read, write):

        async with ClientSession(read, write) as session:

            await session.initialize()

            print("\nConnected to ChargeMate AI Owner MCP Server!")

            # 4. Discover available MCP tools
            mcp_tools = await session.list_tools()

            allowed_tools = {
                "list_my_stations",
                "get_station_details",
                "list_my_chargers",
            }

            openai_tools = [
                {
                    "type": "function",
                    "name": tool.name,
                    "description": tool.description or "",
                    "parameters": tool.inputSchema,
                }
                for tool in mcp_tools.tools
                if tool.name in allowed_tools
            ]

            print("\nAvailable Owner MCP Tools:")

            for tool in openai_tools:
                print("-", tool["name"])

            if not openai_tools:
                print("WARNING: No allowed MCP tools were found.")

            # 5. Maintain conversation history
            conversation = []

            print("\nChargeMate AI Owner Assistant is ready!")
            print("Type 'exit' to stop.\n")

            while True:

                question = input("Owner: ").strip()

                if question.lower() in ["exit", "quit"]:
                    print("Exiting ChargeMate AI...")
                    break

                if not question:
                    continue

                conversation.append({
                    "role": "user",
                    "content": question,
                })

                # 6. Ask OpenAI
                response = await safe_openai_request(
                    openai_client,
                    model=settings.openai_model,
                    instructions=(
                        "You are ChargeMate AI, an assistant "
                        "for electric vehicle charging station owners. "
                        "Use the available MCP tools to answer questions "
                        "about the owner's stations and chargers. "
                        "Never invent database information."
                    ),
                    input=conversation,
                    tools=openai_tools,
                )

                # 7. Handle MCP tool calls
                while True:

                    function_calls = [
                        item
                        for item in response.output
                        if item.type == "function_call"
                    ]

                    # Preserve OpenAI response in conversation
                    conversation.extend(response.output)

                    if not function_calls:
                        break

                    for call in function_calls:

                        print(
                            f"\nExecuting MCP tool: {call.name}"
                        )

                        arguments = json.loads(call.arguments)

                        # Execute the corresponding MCP tool
                        result = await session.call_tool(
                            call.name,
                            arguments=arguments,
                        )

                        result_text = "\n".join(
                            item.text
                            for item in result.content
                            if hasattr(item, "text")
                        )

                        if not result_text:
                            result_text = json.dumps(
                                getattr(
                                    result,
                                    "structuredContent",
                                    {}
                                ),
                                default=str,
                            )

                        if result.isError:
                            result_text = (
                                "MCP tool execution failed: "
                                + result_text
                            )

                        # Return tool result to OpenAI
                        conversation.append({
                            "type": "function_call_output",
                            "call_id": call.call_id,
                            "output": result_text,
                        })

                    # 8. OpenAI processes MCP tool results
                    response = await openai_client.responses.create(
                        model=settings.openai_model,
                        instructions=(
                            "You are ChargeMate AI, an assistant "
                            "for electric vehicle charging station owners. "
                            "Use the available MCP tools to answer questions "
                            "about the owner's stations and chargers. "
                            "Never invent database information."
                        ),
                        input=conversation,
                        tools=openai_tools,
                    )

                # 9. Display final answer
                print("\nChargeMate AI:", response.output_text)
                print()


if __name__ == "__main__":
    asyncio.run(main())
