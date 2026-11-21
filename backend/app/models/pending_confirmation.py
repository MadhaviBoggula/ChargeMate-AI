from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import (
    JSON,
    CheckConstraint,
    DateTime,
    ForeignKey,
    String,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import BaseModel

PENDING_STATUSES = ("pending", "confirmed", "rejected", "expired")


class PendingConfirmation(BaseModel):
    """A server-side operation awaiting an explicit user action.

    The row is created by a sensitive tool (for example
    ``prepare_booking``) or by the chat API when a tool returns a
    confirmation request. It is the single source of truth for what may
    execute on confirmation; the LLM never supplies these values.
    """

    __tablename__ = "pending_confirmations"

    __table_args__ = (
        CheckConstraint(
            "status IN ('pending', 'confirmed', 'rejected', 'expired')",
            name="pending_confirmation_status_valid",
        ),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    conversation_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("conversations.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    action: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    tool: Mapped[str] = mapped_column(
        String(80),
        nullable=False,
    )

    arguments: Mapped[dict] = mapped_column(
        JSON,
        nullable=False,
        default=dict,
    )

    summary: Mapped[dict] = mapped_column(
        JSON,
        nullable=False,
        default=dict,
    )

    status: Mapped[str] = mapped_column(
        String(20),
        default="pending",
        server_default="pending",
        nullable=False,
        index=True,
    )

    expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    resolved_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    result: Mapped[dict | None] = mapped_column(
        JSON,
        nullable=True,
    )

    user: Mapped["User"] = relationship("User")

    conversation: Mapped["Conversation | None"] = relationship(
        "Conversation"
    )
