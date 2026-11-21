
import uuid
from datetime import datetime

from pgvector.sqlalchemy import Vector
from sqlalchemy import (
    DateTime,
    ForeignKey,
    Index,
    Integer,
    JSON,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.core.config import settings
from app.database.base import BaseModel

DOCUMENT_STATUSES = ("pending", "processing", "indexed", "failed")
KNOWLEDGE_ROLES = ("owner", "driver")


class KnowledgeDocument(BaseModel):
    """Metadata record for one ingested knowledge document."""

    __tablename__ = "knowledge_documents"

    role: Mapped[str] = mapped_column(
        String(16),
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
        String(16),
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

    __table_args__ = (
        Index(
            "ix_knowledge_embeddings_vector",
            "embedding",
            postgresql_using="hnsw",
            postgresql_ops={"embedding": "vector_cosine_ops"},
        ),
    )

    document_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey(
            "knowledge_documents.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )
    role: Mapped[str] = mapped_column(
        String(16),
        nullable=False,
        index=True,
    )
    chunk_index: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)
    metadata_: Mapped[dict] = mapped_column(
        "metadata",
        JSONB().with_variant(JSON(), "sqlite"),
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
