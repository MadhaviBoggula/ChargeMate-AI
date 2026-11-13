"""Shared FastAPI dependencies (Member 1's lane - scaffolded contracts).

``get_db`` is the session dependency every protected route uses. The
``current_user`` dependency lands with Member 1's JWT/RBAC work; the expected
signature is documented so routes written now keep working.
"""
from sqlalchemy.orm import Session

from app.database.session import get_db  # re-export for convenience  # noqa: F401


async def current_user():
    """Resolve the authenticated user from the JWT Authorization header.

    Member 1 implements this. Contract:
    - Reads the Bearer token, verifies signature and expiry.
    - Returns an object with ``id``, ``role`` ("owner" | "driver"), and
      ``email``.
    - Raises ``UnauthorizedError`` / ``InvalidTokenError`` from app.core.errors
      on failure.

    Until Member 1 lands it, this fails closed with a 401 rather than
    allowing unauthenticated access.
    """
    from app.core.errors import UnauthorizedError

    raise UnauthorizedError("Authentication is not implemented yet (Member 1).")
