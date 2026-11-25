
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("test-owner-server")


@mcp.tool()
def echo_tool(message: str, auth_context: dict = None) -> dict:
    """Echo the message back."""
    return {"status": "ok", "data": {"echo": message}}


@mcp.tool()
def failing_tool(auth_context: dict = None) -> dict:
    """Always raises an error."""
    raise RuntimeError("simulated tool failure")


@mcp.tool()
def context_echo(auth_context: dict = None) -> dict:
    """Return the trusted context it received."""
    return {"status": "ok", "data": {"received": auth_context}}


if __name__ == "__main__":
    mcp.run()
