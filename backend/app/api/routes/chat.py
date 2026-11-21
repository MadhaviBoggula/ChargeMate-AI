import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
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
from app.mcp.client import MCPConnectionError
from app.models.conversation import Conversation
from app.models.user import User
from app.schemas.chat import ChatRequest, ChatResponse
from app.services import confirmation_service

logger = logging.getLogger("chargemate.chat")

router = APIRouter()

CONFIRMATION_MESSAGE_TYPE = "confirmation_request"


def _pending_from_row(row) -> dict:
    payload = confirmation_service.pending_payload(row)
    arguments = payload.get("arguments") or {}

    # Booking proposals carry the executable proposal id in arguments.
    if arguments.get("proposal_id"):
        payload["proposal_id"] = arguments["proposal_id"]

    return payload


@router.post("", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ChatResponse:
    """
    Authenticated chat entry point.

    The user's role is derived from the verified JWT and selects the
    role-specific workflow. Assistant responses are persisted through the
    shared conversation models, and sensitive operations are tracked in
    the server-side pending_confirmation table.
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

    pending_row = None
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
            pending_row = confirmation_service.get_active_pending(
                db,
                current_user.id,
                conversation_id,
            )

            if pending_row is None:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=(
                        "No pending operation is awaiting confirmation in "
                        "this conversation."
                    ),
                )

            pending_confirmation = _pending_from_row(pending_row)
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
    except MCPConnectionError as exc:
        logger.warning("Chat tool service unavailable: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=(
                "The assistant's tool service is temporarily unavailable. "
                "Try again shortly."
            ),
        )

    returned_pending = result.get("pending_confirmation")
    resolved_pending = None

    if returned_pending:
        row = confirmation_service.persist_pending(
            db,
            current_user.id,
            conversation_id,
            returned_pending,
        )
        resolved_pending = dict(returned_pending)
        resolved_pending.setdefault("proposal_id", str(row.id))
    elif request.confirmation_action:
        confirmation_service.resolve_pending(
            db,
            pending_row,
            status=(
                "confirmed"
                if request.confirmation_action == "confirm"
                else "rejected"
            ),
            result={"tool_results": result.get("tool_results", [])},
        )

    assistant_message_type = (
        CONFIRMATION_MESSAGE_TYPE if resolved_pending else "text"
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
                "pending_confirmation": resolved_pending,
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
        pending_confirmation=resolved_pending,
        message_id=saved.id,
        created_at=saved.created_at,
    )
