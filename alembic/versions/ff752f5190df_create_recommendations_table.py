"""create recommendations table

Revision ID: ff752f5190df
Revises: 930d9507e881
Create Date: 2026-11-18
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "ff752f5190df"
down_revision: Union[str, Sequence[str], None] = "930d9507e881"
branch_labels = None
depends_on = None


def upgrade() -> None:

    op.create_table(
        "recommendations",

        sa.Column(
            "id",
            sa.Integer(),
            primary_key=True,
            index=True
        ),

        sa.Column(
            "station_id",
            sa.Integer(),
            nullable=False
        ),

        sa.Column(
            "recommendation_type",
            sa.String(length=100),
            nullable=False
        ),

        sa.Column(
            "message",
            sa.String(),
            nullable=False
        ),

        sa.Column(
            "priority",
            sa.String(length=50),
            nullable=False
        ),

        sa.Column(
            "confidence",
            sa.Float(),
            nullable=False
        ),

        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now()
        ),
    )


def downgrade() -> None:

    op.drop_table("recommendations")