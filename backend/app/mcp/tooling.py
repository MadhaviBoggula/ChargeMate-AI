from __future__ import annotations

import functools
import logging
import os
from typing import Any

from mcp.server.transport_security import TransportSecuritySettings
from pydantic import ValidationError as PydanticValidationError

from app.core.errors import AppError
from app.mcp.auth import AuthContextError

logger = logging.getLogger("chargemate.mcp.tools")


def ok(data: Any) -> dict[str, Any]:
    return {"status": "ok", "data": data}


def error(detail: str, code: str = "tool_error") -> dict[str, Any]:
    return {"status": "error", "error": code, "detail": detail}


def confirmation_required(
    *,
    tool: str,
    action: str,
    arguments: dict[str, Any],
    summary: dict[str, Any],
    detail: str | None = None,
) -> dict[str, Any]:
    """Return a server-side approval request for a sensitive operation."""

    return {
        "status": "confirmation_required",
        "detail": detail
        or (
            "This operation changes application data and requires an "
            "explicit user confirmation in the application."
        ),
        "confirmation_request": {
            "action": action,
            "tool": tool,
            "arguments": arguments,
            "summary": summary,
        },
    }


def guarded(fn):
    """Convert expected tool failures into structured MCP results."""

    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        try:
            return fn(*args, **kwargs)
        except AuthContextError as exc:
            return error(str(exc), "unauthorized")
        except AppError as exc:
            return error(exc.message, exc.error_code)
        except PydanticValidationError as exc:
            return error(
                f"Invalid tool arguments: {exc.errors()[0].get('msg')}",
                "validation_error",
            )
        except ValueError as exc:
            return error(str(exc), "validation_error")
        except Exception:
            logger.exception("MCP tool '%s' failed", fn.__name__)
            return error(f"Tool '{fn.__name__}' execution failed.")

    return wrapper


def _configure_transport_security(mcp) -> None:
    """Allow the Docker service hostnames while keeping host checks on."""

    current = mcp.settings.transport_security
    configured = os.getenv(
        "MCP_ALLOWED_HOSTS",
        "owner-mcp:*,driver-mcp:*,backend:*",
    )
    hosts = list(current.allowed_hosts)

    for host in configured.split(","):
        host = host.strip()

        if host and host not in hosts:
            hosts.append(host)

    mcp.settings.transport_security = TransportSecuritySettings(
        enable_dns_rebinding_protection=(
            current.enable_dns_rebinding_protection
        ),
        allowed_hosts=hosts,
        allowed_origins=list(current.allowed_origins),
    )


def run_server(
    mcp,
    *,
    default_host: str,
    default_port: int,
) -> None:
    """Run an MCP server over stdio (local) or streamable HTTP (Docker)."""

    transport = os.getenv("MCP_TRANSPORT", "stdio").lower()

    if transport in {"http", "streamable-http", "streamable_http"}:
        mcp.settings.host = os.getenv("MCP_HOST", default_host)
        mcp.settings.port = int(os.getenv("MCP_PORT", str(default_port)))
        _configure_transport_security(mcp)
        logger.info(
            "Starting MCP server '%s' on %s:%s",
            mcp.name,
            mcp.settings.host,
            mcp.settings.port,
        )
        mcp.run(transport="streamable-http")
        return

    if transport == "sse":
        mcp.settings.host = os.getenv("MCP_HOST", default_host)
        mcp.settings.port = int(os.getenv("MCP_PORT", str(default_port)))
        _configure_transport_security(mcp)
        mcp.run(transport="sse")
        return

    mcp.run(transport="stdio")
