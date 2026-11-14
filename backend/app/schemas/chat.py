
import uuid
from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=4000)
    conversation_id: uuid.UUID | None = None
    confirmation_action: Literal["confirm", "reject"] | None = None


class ChatResponse(BaseModel):
    conversation_id: uuid.UUID
    response: str
    route: str
    tool_results: list[dict[str, Any]] = Field(default_factory=list)
    rag_context: list[dict[str, Any]] = Field(default_factory=list)
    pending_confirmation: dict[str, Any] | None = None
    message_id: uuid.UUID | None = None
    created_at: datetime | None = None
