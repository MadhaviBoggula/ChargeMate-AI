"""create driver tables

Revision ID: ba9d0e6efd8e
Revises:
Create Date: 2026-11-11 13:05:42.788930
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "ba9d0e6efd8e"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""

    op.create_table(
        "driver_vehicles",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("driver_id", sa.Integer(), nullable=False),
        sa.Column("vehicle_number", sa.String(length=20), nullable=False),
        sa.Column("vehicle_type", sa.String(length=50), nullable=False),
        sa.Column("battery_capacity", sa.Integer(), nullable=False),
        sa.Column("connector_type", sa.String(length=30), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.ForeignKeyConstraint(["driver_id"], ["drivers.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("vehicle_number"),
    )

    op.create_index(
        op.f("ix_driver_vehicles_id"),
        "driver_vehicles",
        ["id"],
        unique=False,
    )

    op.create_table(
        "favorite_stations",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("driver_id", sa.Integer(), nullable=False),
        sa.Column("station_id", sa.Integer(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.ForeignKeyConstraint(["driver_id"], ["drivers.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_index(
        op.f("ix_favorite_stations_id"),
        "favorite_stations",
        ["id"],
        unique=False,
    )


def downgrade() -> None:
    """Downgrade schema."""

    op.drop_index(
        op.f("ix_favorite_stations_id"),
        table_name="favorite_stations",
    )
    op.drop_table("favorite_stations")

    op.drop_index(
        op.f("ix_driver_vehicles_id"),
        table_name="driver_vehicles",
    )
    op.drop_table("driver_vehicles")