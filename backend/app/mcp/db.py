from __future__ import annotations

from contextlib import contextmanager

from sqlalchemy.orm import Session

from app.database.session import SessionLocal

# Tests replace this with their isolated session factory so MCP tools
# execute against the same database as the API under test.
mcp_session_factory = SessionLocal


@contextmanager
def session_scope() -> Session:
    session = mcp_session_factory()

    try:
        yield session
    finally:
        session.close()
