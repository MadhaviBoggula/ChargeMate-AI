"""Chat orchestration endpoint (Member 4 with Member 1's persistence contract).

Flow: JWT resolves user + role -> load conversation history (Member 1) ->
invoke role graph -> persist messages -> return structured response.
"""
from fastapi import APIRouter

from app.agents.shared.runtime import invoke_graph
from app.api.deps import current_user
from app.core.errors import UnauthorizedError

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("")
async def chat(payload: dict):
    """Authenticated chat entry point (contract with Member 1).

    Request: {"conversation_id": ..., "message": ...}
    Response: {"conversation_id", "response", "route", "pending_confirmation"}
    """
    user = await current_user()  # raises until Member 1's JWT lands
    role = getattr(user, "role", None)
    if role not in {"owner", "driver"}:
        raise UnauthorizedError("Role not recognized for chat.")

    result = await invoke_graph(
        role=role,
        user_id=str(getattr(user, "id", "")),
        conversation_id=payload.get("conversation_id", ""),
        message=payload.get("message", ""),
    )
    return {"conversation_id": payload.get("conversation_id"), **result}
