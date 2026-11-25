"""rag: knowledge_documents and knowledge_embeddings (pgvector)

Revision ID: 0002_rag_knowledge
Revises: 6ceff4e7f9ea
Create Date: 2026-11-14

Owned by Member 4 (RAG lane). Requires the ``vector`` extension on the
target Postgres (Neon has it built in); the upgrade enables it.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from pgvector.sqlalchemy import Vector
from sqlalchemy.dialects.postgresql import JSONB

revision: str = "0002_rag_knowledge"
down_revision: Union[str, None] = "6ceff4e7f9ea"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

VECTOR_DIMS = 384


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    op.create_table(
        "knowledge_documents",
        sa.Column(
            "role",
            sa.String(16),
            sa.CheckConstraint(
                "role IN ('owner','driver')",
                name="ck_knowledge_role",
            ),
            nullable=False,
        ),
        sa.Column("source_filename", sa.String(512), nullable=False),
        sa.Column("source_path", sa.String(1024), nullable=False),
        sa.Column("content_hash", sa.String(64), nullable=False),
        sa.Column(
            "status",
            sa.String(16),
            sa.CheckConstraint(
                "status IN ('pending','processing','indexed','failed')",
                name="ck_knowledge_document_status",
            ),
            nullable=False,
        ),
        sa.Column("chunk_count", sa.Integer, nullable=False),
        sa.Column("error", sa.String(2048), nullable=True),
        sa.Column("ingested_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_knowledge_documents")),
        sa.UniqueConstraint(
            "source_path", name=op.f("uq_knowledge_documents_source_path")
        ),
    )
    op.create_index(
        op.f("ix_knowledge_documents_role"),
        "knowledge_documents",
        ["role"],
        unique=False,
    )
    op.create_index(
        op.f("ix_knowledge_documents_status"),
        "knowledge_documents",
        ["status"],
        unique=False,
    )

    op.create_table(
        "knowledge_embeddings",
        sa.Column(
            "document_id",
            sa.Uuid(),
            nullable=False,
        ),
        sa.Column(
            "role",
            sa.String(16),
            sa.CheckConstraint(
                "role IN ('owner','driver')",
                name="ck_knowledge_role",
            ),
            nullable=False,
        ),
        sa.Column("chunk_index", sa.Integer, nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("metadata", JSONB(), nullable=False),
        sa.Column("embedding", Vector(VECTOR_DIMS), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["document_id"],
            ["knowledge_documents.id"],
            name=op.f("fk_knowledge_embeddings_document_id_knowledge_documents"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_knowledge_embeddings")),
    )
    op.create_index(
        op.f("ix_knowledge_embeddings_document_id"),
        "knowledge_embeddings",
        ["document_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_knowledge_embeddings_role"),
        "knowledge_embeddings",
        ["role"],
        unique=False,
    )
    op.create_index(
        "ix_knowledge_embeddings_vector",
        "knowledge_embeddings",
        ["embedding"],
        unique=False,
        postgresql_using="hnsw",
        postgresql_ops={"embedding": "vector_cosine_ops"},
    )


def downgrade() -> None:
    op.drop_index(
        "ix_knowledge_embeddings_vector", table_name="knowledge_embeddings"
    )
    op.drop_index(
        op.f("ix_knowledge_embeddings_role"),
        table_name="knowledge_embeddings",
    )
    op.drop_index(
        op.f("ix_knowledge_embeddings_document_id"),
        table_name="knowledge_embeddings",
    )
    op.drop_table("knowledge_embeddings")
    op.drop_index(
        op.f("ix_knowledge_documents_status"), table_name="knowledge_documents"
    )
    op.drop_index(
        op.f("ix_knowledge_documents_role"), table_name="knowledge_documents"
    )
    op.drop_table("knowledge_documents")
