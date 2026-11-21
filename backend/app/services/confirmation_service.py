from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.pending_confirmation import PendingConfirmation

DEFAULT_TTL = timedelta(minutes=15)


def _as_uuid(value: Any) -> UUID | None:
    try:
        return UUID(str(value))
    except (TypeError, ValueError):
        return None


def get_active_pending(
    db: Session,
    user_id: UUID,
    conversation_id: UUID,
) -> PendingConfirmation | None:
    """Return the newest pending confirmation for this conversation."""

    row = db.scalar(
        select(PendingConfirmation)
        .where(
            PendingConfirmation.user_id == user_id,
            PendingConfirmation.conversation_id == conversation_id,
            PendingConfirmation.status == "pending",
        )
        .order_by(PendingConfirmation.created_at.desc())
    )

    if row is None:
        return None

    now = datetime.now(timezone.utc)

    if row.expires_at is not None:
        expires_at = row.expires_at

        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)

        if expires_at <= now:
            row.status = "expired"
            row.resolved_at = now
            db.commit()
            return None

    return row


def persist_pending(
    db: Session,
    user_id: UUID,
    conversation_id: UUID,
    pending: dict[str, Any],
) -> PendingConfirmation:
    """Persist a confirmation request emitted by a tool.

    When the tool already created a proposal row (for example
    ``prepare_booking``), that row is reused and linked to the
    conversation instead of duplicating it.
    """

    arguments = dict(pending.get("arguments") or {})
    tool = str(pending.get("tool") or "")
    action = str(pending.get("action") or tool or "operation")
    summary = dict(pending.get("summary") or {})

    row: PendingConfirmation | None = None

    proposal_id = _as_uuid(pending.get("proposal_id")) or _as_uuid(
        arguments.get("proposal_id")
    )

    if proposal_id is not None:
        candidate = db.get(PendingConfirmation, proposal_id)

        if candidate is not None and candidate.user_id == user_id:
            row = candidate

    if row is None:
        row = PendingConfirmation(
            user_id=user_id,
            conversation_id=conversation_id,
            action=action,
            tool=tool,
            arguments=arguments,
            summary=summary,
            status="pending",
            expires_at=datetime.now(timezone.utc) + DEFAULT_TTL,
        )
        db.add(row)
    else:
        # Existing proposal rows keep the executable booking payload;
        # the chat only links them to the conversation.
        row.conversation_id = conversation_id

        if not row.summary and summary:
            row.summary = summary

    db.commit()
    db.refresh(row)
    return row


def resolve_pending(
    db: Session,
    row: PendingConfirmation | None,
    *,
    status: str,
    result: dict[str, Any] | None = None,
) -> None:
    if row is None or row.status != "pending":
        return

    row.status = status
    row.resolved_at = datetime.now(timezone.utc)
    row.result = result
    db.commit()


def pending_payload(row: PendingConfirmation) -> dict[str, Any]:
    return {
        "action": row.action,
        "proposal_id": str(row.id),
        "tool": row.tool,
        "arguments": row.arguments or {},
        "summary": row.summary or {},
    }
