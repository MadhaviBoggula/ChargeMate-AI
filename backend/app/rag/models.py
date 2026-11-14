
import uuid
from datetime import datetime

from pgvector.sqlalchemy import Vector
from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.core.config import settings
from app.database.base import BaseModel

DOCUMENT_STATUSES = ("pending", "processing", "indexed", "failed")
KNOWLEDGE_ROLES = ("owner", "driver")


def _role_enum():
    return Enum(
        *KNOWLEDGE_ROLES,
        name="knowledge_role",
        native_enum=False,
    )


class KnowledgeDocument(BaseModel):
    """Metadata record for one ingested knowledge document."""

    __tablename__ = "knowledge_documents"

    role: Mapped[str] = mapped_column(
        _role_enum(),
        nullable=False,
        index=True,
    )
    source_filename: Mapped[str] = mapped_column(
        String(512),
        nullable=False,
    )
    source_path: Mapped[str] = mapped_column(
        String(1024),
        nullable=False,
        unique=True,
    )
    content_hash: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
    )
    status: Mapped[str] = mapped_column(
        Enum(
            *DOCUMENT_STATUSES,
            name="knowledge_document_status",
            native_enum=False,
        ),
        default="pending",
        nullable=False,
        index=True,
    )
    chunk_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )
    error: Mapped[str | None] = mapped_column(
        String(2048),
        nullable=True,
    )
    ingested_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )


class KnowledgeEmbedding(BaseModel):
    """One chunk of a knowledge document with its vector embedding."""

    __tablename__ = "knowledge_embeddings"

    document_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey(
            "knowledge_documents.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )
    role: Mapped[str] = mapped_column(
        _role_enum(),
        nullable=False,
        index=True,
    )
    chunk_index: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )
    content: Mapped[str] = mapped_column(nullable=False)
    metadata_: Mapped[dict] = mapped_column(
        "metadata",
        JSONB,
        nullable=False,
    )
    embedding = mapped_column(
        Vector(settings.rag_embedding_dimensions),
        nullable=False,
    )


__all__ = [
    "KnowledgeDocument",
    "KnowledgeEmbedding",
    "DOCUMENT_STATUSES",
    "KNOWLEDGE_ROLES",
]
