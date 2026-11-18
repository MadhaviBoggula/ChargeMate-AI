"""add station_id to recommendations

Revision ID: 08bf23f811cd
Revises: ff752f5190df
Create Date: 2026-11-18
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "08bf23f811cd"
down_revision: Union[str, Sequence[str], None] = "ff752f5190df"
branch_labels = None
depends_on = None


def upgrade() -> None:

    # Add station_id
    op.add_column(
        "recommendations",
        sa.Column(
            "station_id",
            sa.Integer(),
            nullable=False,
            server_default="1"
        )
    )

    op.alter_column(
        "recommendations",
        "station_id",
        server_default=None
    )


    # Add recommendation_type
    op.add_column(
        "recommendations",
        sa.Column(
            "recommendation_type",
            sa.String(length=100),
            nullable=False,
            server_default="general"
        )
    )

    op.alter_column(
        "recommendations",
        "recommendation_type",
        server_default=None
    )


    # Add confidence
    op.add_column(
        "recommendations",
        sa.Column(
            "confidence",
            sa.Float(),
            nullable=False,
            server_default="0"
        )
    )

    op.alter_column(
        "recommendations",
        "confidence",
        server_default=None
    )


    # Change message TEXT -> VARCHAR
    op.alter_column(
        "recommendations",
        "message",
        existing_type=sa.TEXT(),
        type_=sa.String(),
        existing_nullable=False
    )


    # Change priority length
    op.alter_column(
        "recommendations",
        "priority",
        existing_type=sa.VARCHAR(length=20),
        type_=sa.String(length=50),
        existing_nullable=False
    )


    # Remove old scenario_id if it exists
    op.drop_constraint(
        "recommendations_scenario_id_fkey",
        "recommendations",
        type_="foreignkey"
    )

    op.drop_column(
        "recommendations",
        "scenario_id"
    )


def downgrade() -> None:

    op.add_column(
        "recommendations",
        sa.Column(
            "scenario_id",
            sa.Integer(),
            nullable=True
        )
    )

    op.add_column(
        "recommendations",
        sa.Column(
            "confidence",
            sa.Float(),
            nullable=False
        )
    )

    op.add_column(
        "recommendations",
        sa.Column(
            "recommendation_type",
            sa.String(length=100),
            nullable=False
        )
    )

    op.add_column(
        "recommendations",
        sa.Column(
            "station_id",
            sa.Integer(),
            nullable=False
        )
    )

    op.alter_column(
        "recommendations",
        "priority",
        existing_type=sa.String(length=50),
        type_=sa.VARCHAR(length=20)
    )