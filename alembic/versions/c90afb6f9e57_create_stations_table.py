"""create stations table

Revision ID: c90afb6f9e57
Revises: c793bb44d863
Create Date: 2026-11-16
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "c90afb6f9e57"
down_revision: Union[str, Sequence[str], None] = "c793bb44d863"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:

    op.create_table(
        "stations",

        sa.Column(
            "id",
            sa.Integer(),
            primary_key=True,
            nullable=False
        ),

        sa.Column(
            "station_name",
            sa.String(),
            nullable=False
        ),

        sa.Column(
            "location",
            sa.String(),
            nullable=False
        ),

        sa.Column(
            "latitude",
            sa.Float(),
            nullable=False
        ),

        sa.Column(
            "longitude",
            sa.Float(),
            nullable=False
        ),

        sa.Column(
            "total_connectors",
            sa.Integer(),
            nullable=False
        ),

        sa.Column(
            "available_connectors",
            sa.Integer(),
            nullable=False
        ),

        sa.Column(
            "charging_speed",
            sa.String(),
            nullable=False
        ),

        sa.Column(
            "status",
            sa.String(),
            nullable=False
        ),

        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True
        )
    )

    op.create_index(
        op.f("ix_stations_id"),
        "stations",
        ["id"],
        unique=False
    )


def downgrade() -> None:

    op.drop_index(
        op.f("ix_stations_id"),
        table_name="stations"
    )

    op.drop_table("stations")