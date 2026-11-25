
import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.agents.shared.context import (
    ConversationNotFoundError,
    load_history,
    save_exchange,
)
from app.agents.shared.runtime import invoke_graph
from app.api.deps import get_current_user
from app.database.session import get_db
from app.llm.client import LLMConfigError, LLMError
from app.models.conversation import Conversation, Message
from app.models.user import User
from app.schemas.chat import ChatRequest, ChatResponse

logger = logging.getLogger("chargemate.chat")

router = APIRouter()

CONFIRMATION_MESSAGE_TYPE = "confirmation_request"


def _load_pending_confirmation(
    db: Session,
    conversation_id: UUID,
) -> dict | None:
    message = db.scalar(
        select(Message)
        .where(
            Message.conversation_id == conversation_id,
            Message.message_type == CONFIRMATION_MESSAGE_TYPE,
        )
        .order_by(Message.created_at.desc())
    )

    if message is None:
        return None

    metadata = message.metadata_json or {}

    return metadata.get("pending_confirmation")


@router.post("", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ChatResponse:
    """
    Authenticated chat entry point.

    The user's role is derived from the verified JWT and selects the
    role-specific workflow. Assistant responses are persisted together
    with the user message through the shared conversation models.
    """

    role = current_user.role.value

    conversation_id = request.conversation_id

    if conversation_id is None and request.confirmation_action:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "A confirmation action requires an existing conversation."
            ),
        )

    pending_confirmation = None

    if conversation_id is not None:
        try:
            history = load_history(
                db,
                current_user.id,
                conversation_id,
            )
        except ConversationNotFoundError:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found.",
            )

        if request.confirmation_action:
            pending_confirmation = _load_pending_confirmation(
                db,
                conversation_id,
            )

            if pending_confirmation is None:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=(
                        "No pending operation is awaiting confirmation in "
                        "this conversation."
                    ),
                )
    else:
        conversation = Conversation(
            user_id=current_user.id,
            title=request.message[:60],
        )

        db.add(conversation)
        db.commit()
        db.refresh(conversation)

        conversation_id = conversation.id
        history = []

    try:
        result = await invoke_graph(
            role=role,
            user_id=str(current_user.id),
            conversation_id=str(conversation_id),
            message=request.message,
            history=history,
            pending_confirmation=pending_confirmation,
            confirmation_action=request.confirmation_action,
        )
    except LLMConfigError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="The assistant is not configured. Contact the operator.",
        )
    except LLMError as exc:
        logger.warning("Chat invocation failed: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="The assistant is temporarily unavailable. Try again.",
        )

    assistant_message_type = (
        CONFIRMATION_MESSAGE_TYPE
        if result.get("pending_confirmation")
        else "text"
    )

    try:
        saved = save_exchange(
            db,
            current_user.id,
            conversation_id,
            user_message=request.message,
            assistant_message=result.get("response", ""),
            assistant_metadata={
                "route": result.get("route"),
                "tool_results": result.get("tool_results", []),
                "rag_context": result.get("rag_context", []),
                "pending_confirmation": result.get(
                    "pending_confirmation"
                ),
            },
            assistant_message_type=assistant_message_type,
        )
    except ConversationNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found.",
        )

    return ChatResponse(
        conversation_id=conversation_id,
        response=result.get("response", ""),
        route=result.get("route", "general"),
        tool_results=result.get("tool_results", []),
        rag_context=result.get("rag_context", []),
        pending_confirmation=result.get("pending_confirmation"),
        message_id=saved.id,
        created_at=saved.created_at,
    )
