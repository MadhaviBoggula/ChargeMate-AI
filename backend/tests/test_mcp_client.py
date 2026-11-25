
import os
import sys

import pytest

from app.mcp.client import MCPToolRegistry

SERVER_SCRIPT = os.path.join(os.path.dirname(__file__), "mcp_test_server.py")

SERVER_URL = f"{sys.executable} {SERVER_SCRIPT}"

TOOL_CONTEXT = {
    "user_id": "12345678-1234-1234-1234-123456789012",
    "role": "owner",
    "conversation_id": "87654321-4321-4321-4321-210987654321",
}


@pytest.fixture
async def registry():
    registry = MCPToolRegistry(role="owner", server_url=SERVER_URL)

    yield registry

    await registry.aclose()


async def test_list_tools_returns_openai_schemas(registry):
    schemas = await registry.list_tools("owner")

    names = [schema["function"]["name"] for schema in schemas]

    assert "echo_tool" in names
    assert "failing_tool" in names
    assert "context_echo" in names

    echo_schema = next(
        schema
        for schema in schemas
        if schema["function"]["name"] == "echo_tool"
    )

    assert echo_schema["type"] == "function"
    assert echo_schema["function"]["description"]
    assert echo_schema["function"]["parameters"]["type"] == "object"


async def test_invoke_tool_success(registry):
    result = await registry.invoke_tool(
        "owner", "echo_tool", {"message": "hello"}, TOOL_CONTEXT
    )

    assert result["status"] == "ok"
    assert result["data"]["echo"] == "hello"


async def test_invoke_tool_error_is_normalized(registry):
    result = await registry.invoke_tool(
        "owner", "failing_tool", {}, TOOL_CONTEXT
    )

    assert result["status"] == "error"
    assert "simulated tool failure" in result["detail"]


async def test_trusted_context_is_propagated(registry):
    result = await registry.invoke_tool(
        "owner", "context_echo", {}, TOOL_CONTEXT
    )

    received = result["data"]["received"]

    assert received["user_id"] == TOOL_CONTEXT["user_id"]
    assert received["role"] == "owner"
    assert received["conversation_id"] == TOOL_CONTEXT["conversation_id"]


async def test_sequential_invocations_all_succeed(registry):
    first = await registry.invoke_tool(
        "owner", "echo_tool", {"message": "one"}, TOOL_CONTEXT
    )
    second = await registry.invoke_tool(
        "owner", "echo_tool", {"message": "two"}, TOOL_CONTEXT
    )

    assert first["data"]["echo"] == "one"
    assert second["data"]["echo"] == "two"


async def test_schemas_hide_reserved_context_argument(registry):
    schemas = await registry.list_tools("owner")

    for schema in schemas:
        parameters = schema["function"]["parameters"]

        assert registry.RESERVED_CONTEXT_KEY not in parameters.get(
            "properties", {}
        )
        assert registry.RESERVED_CONTEXT_KEY not in parameters.get(
            "required", []
        )


async def test_llm_supplied_context_is_overwritten_with_trusted_context(
    registry,
):
    result = await registry.invoke_tool(
        "owner",
        "context_echo",
        {
            "auth_context": {
                "user_id": "spoofed-user",
                "role": "owner",
            }
        },
        TOOL_CONTEXT,
    )

    received = result["data"]["received"]

    assert received["user_id"] == TOOL_CONTEXT["user_id"]
    assert "spoofed-user" not in str(received)


async def test_unavailable_server_raises_connection_error():
    registry = MCPToolRegistry(
        role="owner",
        server_url=f"{sys.executable} {os.path.join(os.path.dirname(__file__), 'does_not_exist.py')}",
    )

    with pytest.raises(Exception):
        await registry.list_tools("owner")
