"""Trusted identity context for MCP tool execution.

The backend's MCP client injects ``auth_context`` into every call and
removes any model-supplied value. Tools must derive the acting user from
this context and validate the role against their own server role.
"""
from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.user import User


class AuthContextError(ValueError):
    """Raised when a tool is called without valid trusted identity."""


@dataclass(frozen=True)
class AuthContext:
    user_id: UUID
    role: str
    conversation_id: UUID | None
    approved: bool

    def as_dict(self) -> dict:
        return {
            "user_id": str(self.user_id),
            "role": self.role,
            "conversation_id": (
                str(self.conversation_id) if self.conversation_id else None
            ),
            "approved": self.approved,
        }


def _parse_uuid(value: object, field: str) -> UUID:
    try:
        return UUID(str(value))
    except (TypeError, ValueError) as exc:
        raise AuthContextError(
            f"auth_context.{field} must be a valid UUID."
        ) from exc


def parse_auth_context(
    value: object,
    expected_role: str,
) -> AuthContext:
    if not isinstance(value, dict):
        raise AuthContextError(
            "auth_context is required and must be supplied by the backend."
        )

    role = str(value.get("role") or "").lower()

    if role != expected_role:
        raise AuthContextError(
            f"This tool requires the '{expected_role}' role; "
            "the supplied identity does not match."
        )

    user_id = _parse_uuid(value.get("user_id"), "user_id")

    conversation_id = None

    if value.get("conversation_id"):
        conversation_id = _parse_uuid(
            value.get("conversation_id"),
            "conversation_id",
        )

    return AuthContext(
        user_id=user_id,
        role=role,
        conversation_id=conversation_id,
        approved=value.get("approved") is True,
    )


def resolve_user(
    db: Session,
    context: AuthContext,
    expected_role: str,
) -> User:
    """Verify the identity still exists, is active, and has the role."""

    user = db.get(User, context.user_id)

    if user is None or not user.is_active:
        raise AuthContextError("The authenticated user no longer exists.")

    role = user.role.value if hasattr(user.role, "value") else str(user.role)

    if role != expected_role:
        raise AuthContextError(
            "The authenticated user does not have the required role."
        )

    return user
