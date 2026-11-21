"""owner domain: stations, chargers, connectors, charging sessions

Revision ID: 0003_owner_domain
Revises: 0002_rag_knowledge
Create Date: 2026-11-21

Stations embed their address fields; connectors are normalized per
charger. Charging sessions carry the energy and price snapshot that
owner revenue and analytics are derived from.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0003_owner_domain"
down_revision: Union[str, None] = "0002_rag_knowledge"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "stations",
        sa.Column("owner_id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.String(1000), nullable=True),
        sa.Column("address_line1", sa.String(255), nullable=True),
        sa.Column("address_line2", sa.String(255), nullable=True),
        sa.Column("city", sa.String(100), nullable=False),
        sa.Column("state", sa.String(100), nullable=False),
        sa.Column("pincode", sa.String(10), nullable=False),
        sa.Column("latitude", sa.Float(), nullable=True),
        sa.Column("longitude", sa.Float(), nullable=True),
        sa.Column(
            "timezone",
            sa.String(64),
            server_default="Asia/Kolkata",
            nullable=False,
        ),
        sa.Column(
            "is_active",
            sa.Boolean(),
            server_default=sa.text("true"),
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
        sa.CheckConstraint(
            "latitude IS NULL OR (latitude >= -90 AND latitude <= 90)",
            name="ck_stations_station_latitude_range",
        ),
        sa.CheckConstraint(
            "longitude IS NULL OR (longitude >= -180 AND longitude <= 180)",
            name="ck_stations_station_longitude_range",
        ),
        sa.ForeignKeyConstraint(
            ["owner_id"],
            ["users.id"],
            name="fk_stations_owner_id_users",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_stations"),
    )
    op.create_index("ix_stations_owner_id", "stations", ["owner_id"])
    op.create_index("ix_stations_name", "stations", ["name"])
    op.create_index("ix_stations_city", "stations", ["city"])
    op.create_index("ix_stations_pincode", "stations", ["pincode"])
    op.create_index("ix_stations_is_active", "stations", ["is_active"])

    op.create_table(
        "chargers",
        sa.Column("station_id", sa.Uuid(), nullable=False),
        sa.Column("charger_code", sa.String(80), nullable=False),
        sa.Column("charging_type", sa.String(2), nullable=False),
        sa.Column("power_kw", sa.Numeric(8, 2), nullable=False),
        sa.Column(
            "status",
            sa.String(20),
            server_default="active",
            nullable=False,
        ),
        sa.Column(
            "availability",
            sa.String(20),
            server_default="available",
            nullable=False,
        ),
        sa.Column(
            "price_per_kwh",
            sa.Numeric(10, 2),
            server_default="0.00",
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
        sa.CheckConstraint(
            "charging_type IN ('AC', 'DC')",
            name="ck_chargers_charger_charging_type_valid",
        ),
        sa.CheckConstraint(
            "power_kw > 0",
            name="ck_chargers_charger_power_positive",
        ),
        sa.CheckConstraint(
            "price_per_kwh >= 0",
            name="ck_chargers_charger_price_nonnegative",
        ),
        sa.CheckConstraint(
            "status IN ('active', 'inactive', 'maintenance', 'faulted')",
            name="ck_chargers_charger_status_valid",
        ),
        sa.CheckConstraint(
            "availability IN ('available', 'occupied', 'unavailable')",
            name="ck_chargers_charger_availability_valid",
        ),
        sa.ForeignKeyConstraint(
            ["station_id"],
            ["stations.id"],
            name="fk_chargers_station_id_stations",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_chargers"),
        sa.UniqueConstraint(
            "charger_code",
            name="uq_chargers_charger_code",
        ),
    )
    op.create_index("ix_chargers_station_id", "chargers", ["station_id"])
    op.create_index("ix_chargers_charger_code", "chargers", ["charger_code"])
    op.create_index("ix_chargers_status", "chargers", ["status"])
    op.create_index(
        "ix_chargers_availability",
        "chargers",
        ["availability"],
    )

    op.create_table(
        "connectors",
        sa.Column("charger_id", sa.Uuid(), nullable=False),
        sa.Column("connector_type", sa.String(50), nullable=False),
        sa.Column("power_kw", sa.Numeric(8, 2), nullable=False),
        sa.Column(
            "status",
            sa.String(20),
            server_default="active",
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
        sa.CheckConstraint(
            "power_kw > 0",
            name="ck_connectors_connector_power_positive",
        ),
        sa.CheckConstraint(
            "status IN ('active', 'inactive', 'faulted')",
            name="ck_connectors_connector_status_valid",
        ),
        sa.ForeignKeyConstraint(
            ["charger_id"],
            ["chargers.id"],
            name="fk_connectors_charger_id_chargers",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_connectors"),
        sa.UniqueConstraint(
            "charger_id",
            "connector_type",
            name="uq_connectors_charger_type",
        ),
    )
    op.create_index(
        "ix_connectors_charger_id",
        "connectors",
        ["charger_id"],
    )
    op.create_index(
        "ix_connectors_connector_type",
        "connectors",
        ["connector_type"],
    )
    op.create_index("ix_connectors_status", "connectors", ["status"])

    op.create_table(
        "charging_sessions",
        sa.Column("station_id", sa.Uuid(), nullable=False),
        sa.Column("charger_id", sa.Uuid(), nullable=False),
        sa.Column("driver_id", sa.Uuid(), nullable=True),
        sa.Column("booking_id", sa.Uuid(), nullable=True),
        sa.Column(
            "started_at",
            sa.DateTime(timezone=True),
            nullable=False,
        ),
        sa.Column(
            "ended_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
        sa.Column(
            "energy_kwh",
            sa.Numeric(10, 3),
            server_default="0.000",
            nullable=False,
        ),
        sa.Column(
            "duration_minutes",
            sa.Integer(),
            server_default="0",
            nullable=False,
        ),
        sa.Column(
            "price_per_kwh",
            sa.Numeric(10, 2),
            server_default="0.00",
            nullable=False,
        ),
        sa.Column(
            "revenue",
            sa.Numeric(12, 2),
            server_default="0.00",
            nullable=False,
        ),
        sa.Column(
            "status",
            sa.String(20),
            server_default="completed",
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
        sa.CheckConstraint(
            "energy_kwh >= 0",
            name="ck_charging_sessions_session_energy_nonnegative",
        ),
        sa.CheckConstraint(
            "duration_minutes >= 0",
            name="ck_charging_sessions_session_duration_nonnegative",
        ),
        sa.CheckConstraint(
            "price_per_kwh >= 0",
            name="ck_charging_sessions_session_price_nonnegative",
        ),
        sa.CheckConstraint(
            "revenue >= 0",
            name="ck_charging_sessions_session_revenue_nonnegative",
        ),
        sa.CheckConstraint(
            "status IN ('active', 'completed', 'cancelled', 'failed')",
            name="ck_charging_sessions_session_status_valid",
        ),
        sa.CheckConstraint(
            "ended_at IS NULL OR ended_at >= started_at",
            name="ck_charging_sessions_session_end_after_start",
        ),
        sa.ForeignKeyConstraint(
            ["station_id"],
            ["stations.id"],
            name="fk_charging_sessions_station_id_stations",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["charger_id"],
            ["chargers.id"],
            name="fk_charging_sessions_charger_id_chargers",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["driver_id"],
            ["users.id"],
            name="fk_charging_sessions_driver_id_users",
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_charging_sessions"),
    )
    op.create_index(
        "ix_charging_sessions_station_id",
        "charging_sessions",
        ["station_id"],
    )
    op.create_index(
        "ix_charging_sessions_charger_id",
        "charging_sessions",
        ["charger_id"],
    )
    op.create_index(
        "ix_charging_sessions_driver_id",
        "charging_sessions",
        ["driver_id"],
    )
    op.create_index(
        "ix_charging_sessions_booking_id",
        "charging_sessions",
        ["booking_id"],
    )
    op.create_index(
        "ix_charging_sessions_started_at",
        "charging_sessions",
        ["started_at"],
    )
    op.create_index(
        "ix_charging_sessions_status",
        "charging_sessions",
        ["status"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_charging_sessions_status",
        table_name="charging_sessions",
    )
    op.drop_index(
        "ix_charging_sessions_started_at",
        table_name="charging_sessions",
    )
    op.drop_index(
        "ix_charging_sessions_booking_id",
        table_name="charging_sessions",
    )
    op.drop_index(
        "ix_charging_sessions_driver_id",
        table_name="charging_sessions",
    )
    op.drop_index(
        "ix_charging_sessions_charger_id",
        table_name="charging_sessions",
    )
    op.drop_index(
        "ix_charging_sessions_station_id",
        table_name="charging_sessions",
    )
    op.drop_table("charging_sessions")

    op.drop_index("ix_connectors_status", table_name="connectors")
    op.drop_index(
        "ix_connectors_connector_type",
        table_name="connectors",
    )
    op.drop_index("ix_connectors_charger_id", table_name="connectors")
    op.drop_table("connectors")

    op.drop_index("ix_chargers_availability", table_name="chargers")
    op.drop_index("ix_chargers_status", table_name="chargers")
    op.drop_index("ix_chargers_charger_code", table_name="chargers")
    op.drop_index("ix_chargers_station_id", table_name="chargers")
    op.drop_table("chargers")

    op.drop_index("ix_stations_is_active", table_name="stations")
    op.drop_index("ix_stations_pincode", table_name="stations")
    op.drop_index("ix_stations_city", table_name="stations")
    op.drop_index("ix_stations_name", table_name="stations")
    op.drop_index("ix_stations_owner_id", table_name="stations")
    op.drop_table("stations")
