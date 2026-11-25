
"""create bookings table

Revision ID: c642fc8a5bb5
Revises: c71a4e92d630
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "c642fc8a5bb5"
down_revision: Union[str, Sequence[str], None] = "c71a4e92d630"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "bookings",
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("station_id", sa.Uuid(), nullable=False),
        sa.Column("booking_time", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "status",
            sa.String(length=20),
            server_default="Pending",
            nullable=False,
        ),
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
            ["user_id"],
            ["users.id"],
            name="fk_bookings_user_id_users",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["station_id"],
            ["stations.id"],
            name="fk_bookings_station_id_stations",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_bookings"),
    )

    op.create_index(
        "ix_bookings_user_id",
        "bookings",
        ["user_id"],
        unique=False,
    )
    op.create_index(
        "ix_bookings_station_id",
        "bookings",
        ["station_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_bookings_station_id", table_name="bookings")
    op.drop_index("ix_bookings_user_id", table_name="bookings")
    op.drop_table("bookings")
