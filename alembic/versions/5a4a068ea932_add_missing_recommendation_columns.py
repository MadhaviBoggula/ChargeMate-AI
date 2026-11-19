"""add missing recommendation columns

Revision ID: 5a4a068ea932
Revises: 08bf23f811cd
Create Date: 2026-11-18
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "5a4a068ea932"
down_revision: Union[str, Sequence[str], None] = "08bf23f811cd"
branch_labels = None
depends_on = None


def upgrade() -> None:

    # Add missing recommendation_type column
    op.add_column(
        "recommendations",
        sa.Column(
            "recommendation_type",
            sa.String(length=100),
            nullable=False,
            server_default="general"
        )
    )

    # Add missing confidence column
    op.add_column(
        "recommendations",
        sa.Column(
            "confidence",
            sa.Float(),
            nullable=True
        )
    )

    # Update message column type
    op.alter_column(
        "recommendations",
        "message",
        existing_type=sa.TEXT(),
        type_=sa.String(),
        existing_nullable=True
    )

    # Update priority column type
    op.alter_column(
        "recommendations",
        "priority",
        existing_type=sa.String(length=20),
        type_=sa.String(length=50),
        existing_nullable=True
    )


def downgrade() -> None:

    # Revert priority type
    op.alter_column(
        "recommendations",
        "priority",
        existing_type=sa.String(length=50),
        type_=sa.String(length=20),
        existing_nullable=True
    )

    # Revert message type
    op.alter_column(
        "recommendations",
        "message",
        existing_type=sa.String(),
        type_=sa.TEXT(),
        existing_nullable=True
    )

    # Remove confidence column
    op.drop_column(
        "recommendations",
        "confidence"
    )

    # Remove recommendation_type column
    op.drop_column(
        "recommendations",
        "recommendation_type"
    )