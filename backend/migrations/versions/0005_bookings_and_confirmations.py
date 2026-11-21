"""bookings and server-side pending confirmations

Revision ID: 0005_bookings
Revises: 0004_driver_domain
Create Date: 2026-11-21

Charging bookings store fixed 30-minute reservations in UTC. On
PostgreSQL a GiST exclusion constraint makes overlapping CONFIRMED
bookings on the same charger impossible even under concurrency.
Pending confirmations are the server-side source of truth for
operations that require an explicit user action.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0005_bookings"
down_revision: Union[str, None] = "0004_driver_domain"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "charging_bookings",
        sa.Column("booking_reference", sa.String(32), nullable=False),
        sa.Column("driver_id", sa.Uuid(), nullable=False),
        sa.Column("station_id", sa.Uuid(), nullable=False),
        sa.Column("charger_id", sa.Uuid(), nullable=False),
        sa.Column("vehicle_id", sa.Uuid(), nullable=True),
        sa.Column("connector_type", sa.String(50), nullable=False),
        sa.Column("start_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("end_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "status",
            sa.String(20),
            server_default="CONFIRMED",
            nullable=False,
        ),
        sa.Column(
            "estimated_price",
            sa.Numeric(12, 2),
            nullable=True,
        ),
        sa.Column(
            "cancelled_at",
            sa.DateTime(timezone=True),
            nullable=True,
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
        sa.CheckConstraint(
            "status IN ('CONFIRMED', 'CANCELLED', 'COMPLETED', 'EXPIRED')",
            name="ck_charging_bookings_booking_status_valid",
        ),
        sa.CheckConstraint(
            "end_at > start_at",
            name="ck_charging_bookings_booking_end_after_start",
        ),
        sa.CheckConstraint(
            "estimated_price IS NULL OR estimated_price >= 0",
            name="ck_charging_bookings_booking_price_nonnegative",
        ),
        sa.ForeignKeyConstraint(
            ["driver_id"],
            ["users.id"],
            name="fk_charging_bookings_driver_id_users",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["station_id"],
            ["stations.id"],
            name="fk_charging_bookings_station_id_stations",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["charger_id"],
            ["chargers.id"],
            name="fk_charging_bookings_charger_id_chargers",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["vehicle_id"],
            ["vehicles.id"],
            name="fk_charging_bookings_vehicle_id_vehicles",
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_charging_bookings"),
        sa.UniqueConstraint(
            "booking_reference",
            name="uq_charging_bookings_booking_reference",
        ),
    )
    op.create_index(
        "ix_charging_bookings_booking_reference",
        "charging_bookings",
        ["booking_reference"],
    )
    op.create_index(
        "ix_charging_bookings_driver_id",
        "charging_bookings",
        ["driver_id"],
    )
    op.create_index(
        "ix_charging_bookings_station_id",
        "charging_bookings",
        ["station_id"],
    )
    op.create_index(
        "ix_charging_bookings_charger_id",
        "charging_bookings",
        ["charger_id"],
    )
    op.create_index(
        "ix_charging_bookings_connector_type",
        "charging_bookings",
        ["connector_type"],
    )
    op.create_index(
        "ix_charging_bookings_start_at",
        "charging_bookings",
        ["start_at"],
    )
    op.create_index(
        "ix_charging_bookings_end_at",
        "charging_bookings",
        ["end_at"],
    )
    op.create_index(
        "ix_charging_bookings_status",
        "charging_bookings",
        ["status"],
    )
    op.create_index(
        "ix_charging_bookings_charger_start",
        "charging_bookings",
        ["charger_id", "start_at"],
    )

    if op.get_bind().dialect.name == "postgresql":
        op.execute("CREATE EXTENSION IF NOT EXISTS btree_gist")
        op.execute(
            """
            ALTER TABLE charging_bookings
            ADD CONSTRAINT ex_charging_bookings_no_overlap
            EXCLUDE USING gist (
                charger_id WITH =,
                tstzrange(start_at, end_at) WITH &&
            )
            WHERE (status = 'CONFIRMED')
            """
        )

    op.create_table(
        "pending_confirmations",
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("conversation_id", sa.Uuid(), nullable=True),
        sa.Column("action", sa.String(50), nullable=False),
        sa.Column("tool", sa.String(80), nullable=False),
        sa.Column("arguments", sa.JSON(), nullable=False),
        sa.Column("summary", sa.JSON(), nullable=False),
        sa.Column(
            "status",
            sa.String(20),
            server_default="pending",
            nullable=False,
        ),
        sa.Column(
            "expires_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
        sa.Column(
            "resolved_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
        sa.Column("result", sa.JSON(), nullable=True),
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
        sa.CheckConstraint(
            "status IN ('pending', 'confirmed', 'rejected', 'expired')",
            name="ck_pending_confirmations_pending_confirmation_status_valid",
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name="fk_pending_confirmations_user_id_users",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["conversation_id"],
            ["conversations.id"],
            name="fk_pending_confirmations_conversation_id_conversations",
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_pending_confirmations"),
    )
    op.create_index(
        "ix_pending_confirmations_user_id",
        "pending_confirmations",
        ["user_id"],
    )
    op.create_index(
        "ix_pending_confirmations_conversation_id",
        "pending_confirmations",
        ["conversation_id"],
    )
    op.create_index(
        "ix_pending_confirmations_status",
        "pending_confirmations",
        ["status"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_pending_confirmations_status",
        table_name="pending_confirmations",
    )
    op.drop_index(
        "ix_pending_confirmations_conversation_id",
        table_name="pending_confirmations",
    )
    op.drop_index(
        "ix_pending_confirmations_user_id",
        table_name="pending_confirmations",
    )
    op.drop_table("pending_confirmations")

    if op.get_bind().dialect.name == "postgresql":
        op.execute(
            "ALTER TABLE charging_bookings "
            "DROP CONSTRAINT IF EXISTS ex_charging_bookings_no_overlap"
        )

    op.drop_index(
        "ix_charging_bookings_charger_start",
        table_name="charging_bookings",
    )
    op.drop_index(
        "ix_charging_bookings_status",
        table_name="charging_bookings",
    )
    op.drop_index(
        "ix_charging_bookings_end_at",
        table_name="charging_bookings",
    )
    op.drop_index(
        "ix_charging_bookings_start_at",
        table_name="charging_bookings",
    )
    op.drop_index(
        "ix_charging_bookings_connector_type",
        table_name="charging_bookings",
    )
    op.drop_index(
        "ix_charging_bookings_charger_id",
        table_name="charging_bookings",
    )
    op.drop_index(
        "ix_charging_bookings_station_id",
        table_name="charging_bookings",
    )
    op.drop_index(
        "ix_charging_bookings_driver_id",
        table_name="charging_bookings",
    )
    op.drop_index(
        "ix_charging_bookings_booking_reference",
        table_name="charging_bookings",
    )
    op.drop_table("charging_bookings")
