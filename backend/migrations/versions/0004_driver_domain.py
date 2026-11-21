"""driver domain: vehicles, driver preferences, favourite stations

Revision ID: 0004_driver_domain
Revises: 0003_owner_domain
Create Date: 2026-11-21

Driver identity lives in ``users`` (role=driver). These tables add the
driver-owned data used for compatibility checks, discovery, and bookings.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0004_driver_domain"
down_revision: Union[str, None] = "0003_owner_domain"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "vehicles",
        sa.Column("driver_id", sa.Uuid(), nullable=False),
        sa.Column("registration_number", sa.String(32), nullable=False),
        sa.Column("nickname", sa.String(80), nullable=True),
        sa.Column("vehicle_model", sa.String(120), nullable=True),
        sa.Column(
            "vehicle_type",
            sa.String(50),
            server_default="car",
            nullable=False,
        ),
        sa.Column("manufacturing_year", sa.Integer(), nullable=True),
        sa.Column(
            "battery_capacity_kwh",
            sa.Numeric(7, 2),
            nullable=True,
        ),
        sa.Column("connector_type", sa.String(50), nullable=False),
        sa.Column(
            "is_primary",
            sa.Boolean(),
            server_default=sa.text("false"),
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
            "manufacturing_year IS NULL OR "
            "(manufacturing_year >= 1950 AND manufacturing_year <= 2100)",
            name="ck_vehicles_vehicle_year_range",
        ),
        sa.CheckConstraint(
            "battery_capacity_kwh IS NULL OR battery_capacity_kwh > 0",
            name="ck_vehicles_vehicle_battery_positive",
        ),
        sa.ForeignKeyConstraint(
            ["driver_id"],
            ["users.id"],
            name="fk_vehicles_driver_id_users",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_vehicles"),
        sa.UniqueConstraint(
            "driver_id",
            "registration_number",
            name="uq_vehicles_driver_registration",
        ),
    )
    op.create_index("ix_vehicles_driver_id", "vehicles", ["driver_id"])
    op.create_index(
        "ix_vehicles_connector_type",
        "vehicles",
        ["connector_type"],
    )

    op.create_table(
        "driver_preferences",
        sa.Column("driver_id", sa.Uuid(), nullable=False),
        sa.Column(
            "preferred_connector_type",
            sa.String(50),
            nullable=True,
        ),
        sa.Column(
            "preferred_charging_type",
            sa.String(2),
            nullable=True,
        ),
        sa.Column(
            "max_price_per_kwh",
            sa.Numeric(10, 2),
            nullable=True,
        ),
        sa.Column("preferred_city", sa.String(100), nullable=True),
        sa.Column("default_vehicle_id", sa.Uuid(), nullable=True),
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
            "preferred_charging_type IS NULL OR "
            "preferred_charging_type IN ('AC', 'DC')",
            name="ck_driver_preferences_driver_preference_charging_type_valid",
        ),
        sa.CheckConstraint(
            "max_price_per_kwh IS NULL OR max_price_per_kwh >= 0",
            name="ck_driver_preferences_driver_preference_price_nonnegative",
        ),
        sa.ForeignKeyConstraint(
            ["driver_id"],
            ["users.id"],
            name="fk_driver_preferences_driver_id_users",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["default_vehicle_id"],
            ["vehicles.id"],
            name="fk_driver_preferences_default_vehicle_id_vehicles",
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_driver_preferences"),
        sa.UniqueConstraint(
            "driver_id",
            name="uq_driver_preferences_driver_id",
        ),
    )
    op.create_table(
        "favourite_stations",
        sa.Column("driver_id", sa.Uuid(), nullable=False),
        sa.Column("station_id", sa.Uuid(), nullable=False),
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
            ["driver_id"],
            ["users.id"],
            name="fk_favourite_stations_driver_id_users",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["station_id"],
            ["stations.id"],
            name="fk_favourite_stations_station_id_stations",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_favourite_stations"),
        sa.UniqueConstraint(
            "driver_id",
            "station_id",
            name="uq_favourite_stations_driver_station",
        ),
    )
    op.create_index(
        "ix_favourite_stations_driver_id",
        "favourite_stations",
        ["driver_id"],
    )
    op.create_index(
        "ix_favourite_stations_station_id",
        "favourite_stations",
        ["station_id"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_favourite_stations_station_id",
        table_name="favourite_stations",
    )
    op.drop_index(
        "ix_favourite_stations_driver_id",
        table_name="favourite_stations",
    )
    op.drop_table("favourite_stations")

    op.drop_table("driver_preferences")

    op.drop_index(
        "ix_vehicles_connector_type",
        table_name="vehicles",
    )
    op.drop_index("ix_vehicles_driver_id", table_name="vehicles")
    op.drop_table("vehicles")
