"""add addresses and UUID-based chargers

Revision ID: c71a4e92d630
Revises: 042b1a0729ae
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "c71a4e92d630"
down_revision: Union[str, Sequence[str], None] = "042b1a0729ae"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Create structured addresses.
    op.create_table(
        "addresses",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("hno", sa.String(length=50), nullable=True),
        sa.Column("street_village", sa.String(length=255), nullable=False),
        sa.Column("city", sa.String(length=100), nullable=False),
        sa.Column("state", sa.String(length=100), nullable=False),
        sa.Column("pincode", sa.String(length=10), nullable=False),
        sa.Column("lat", sa.Float(), nullable=True),
        sa.Column("long", sa.Float(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )

    op.create_index("ix_addresses_id", "addresses", ["id"])
    op.create_index("ix_addresses_city", "addresses", ["city"])
    op.create_index("ix_addresses_pincode", "addresses", ["pincode"])

    # 2. Add an optional structured address to existing UUID stations.
    # Existing station records remain valid with address_id = NULL.
    op.add_column(
        "stations",
        sa.Column("address_id", sa.Integer(), nullable=True),
    )

    op.create_foreign_key(
        "fk_stations_address_id_addresses",
        "stations",
        "addresses",
        ["address_id"],
        ["id"],
        ondelete="SET NULL",
    )

    op.create_index(
        "ix_stations_address_id",
        "stations",
        ["address_id"],
        unique=False,
    )

    # 3. Create chargers linked to the existing UUID stations table.
    op.create_table(
        "chargers",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column(
            "station_id",
            sa.Uuid(as_uuid=True),
            nullable=False,
        ),
        sa.Column("charger_code", sa.String(length=80), nullable=False),
        sa.Column("connector_type", sa.String(length=50), nullable=False),
        sa.Column("charging_type", sa.String(length=2), nullable=False),
        sa.Column("power_kw", sa.Numeric(8, 2), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("availability", sa.String(length=20), nullable=False),
        sa.Column("price_per_kwh", sa.Numeric(10, 2), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["station_id"],
            ["stations.id"],
            name="fk_chargers_station_id_stations",
            ondelete="CASCADE",
        ),
    )

    op.create_index("ix_chargers_id", "chargers", ["id"])
    op.create_index(
        "ix_chargers_station_id",
        "chargers",
        ["station_id"],
        unique=False,
    )
    op.create_index(
        "ix_chargers_charger_code",
        "chargers",
        ["charger_code"],
        unique=True,
    )


def downgrade() -> None:
    # Remove only objects introduced by this migration.
    op.drop_index("ix_chargers_charger_code", table_name="chargers")
    op.drop_index("ix_chargers_station_id", table_name="chargers")
    op.drop_index("ix_chargers_id", table_name="chargers")
    op.drop_table("chargers")

    op.drop_index("ix_stations_address_id", table_name="stations")
    op.drop_constraint(
        "fk_stations_address_id_addresses",
        "stations",
        type_="foreignkey",
    )
    op.drop_column("stations", "address_id")

    op.drop_index("ix_addresses_pincode", table_name="addresses")
    op.drop_index("ix_addresses_city", table_name="addresses")
    op.drop_index("ix_addresses_id", table_name="addresses")
    op.drop_table("addresses")
