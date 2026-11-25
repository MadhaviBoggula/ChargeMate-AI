
from datetime import datetime, timedelta, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.conversation import Conversation, Message, MessageRole


class ConversationNotFoundError(Exception):
    """Raised when a conversation does not exist for the user."""


_ROLE_TO_MESSAGE_ROLE = {
    "user": MessageRole.USER,
    "assistant": MessageRole.ASSISTANT,
    "system": MessageRole.SYSTEM,
    "tool": MessageRole.TOOL,
}


def _get_owned_conversation(
    db: Session,
    user_id: UUID,
    conversation_id: UUID,
) -> Conversation | None:
    return db.scalar(
        select(Conversation).where(
            Conversation.id == conversation_id,
            Conversation.user_id == user_id,
        )
    )


def load_history(
    db: Session,
    user_id: UUID,
    conversation_id: UUID,
    limit: int = 20,
) -> list[dict[str, str]]:
    """
    Load recent conversation history for the authenticated user.

    Ownership is enforced here: the conversation must belong to the
    user derived from the verified JWT context.
    """

    conversation = _get_owned_conversation(db, user_id, conversation_id)

    if conversation is None:
        raise ConversationNotFoundError(
            "Conversation not found for the authenticated user."
        )

    statement = (
        select(Message)
        .where(
            Message.conversation_id == conversation.id,
            Message.role != MessageRole.TOOL,
        )
        .order_by(Message.created_at.desc())
        .limit(limit)
    )

    messages = list(db.scalars(statement))

    history = []

    for message in reversed(messages):
        history.append(
            {
                "role": message.role.value,
                "content": message.content,
            }
        )

    return history


def save_exchange(
    db: Session,
    user_id: UUID,
    conversation_id: UUID,
    user_message: str,
    assistant_message: str,
    assistant_metadata: dict | None = None,
    assistant_message_type: str = "text",
) -> Message:
    """
    Persist one user message and one assistant message.

    Ownership is enforced here: the conversation must belong to the
    user derived from the verified JWT context.
    """

    conversation = _get_owned_conversation(db, user_id, conversation_id)

    if conversation is None:
        raise ConversationNotFoundError(
            "Conversation not found for the authenticated user."
        )

    now = datetime.now(timezone.utc)

    user_row = Message(
        conversation_id=conversation.id,
        role=MessageRole.USER,
        content=user_message,
        created_at=now,
    )
    assistant_row = Message(
        conversation_id=conversation.id,
        role=MessageRole.ASSISTANT,
        content=assistant_message,
        message_type=assistant_message_type,
        metadata_json=assistant_metadata,
        created_at=now + timedelta(microseconds=1),
    )

    db.add(user_row)
    db.add(assistant_row)
    db.commit()

    return assistant_row
