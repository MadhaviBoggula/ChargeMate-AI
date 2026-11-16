"""create address, charging station and charger tables

Revision ID: 0001_address_station_charger
Revises:
"""
from alembic import op
import sqlalchemy as sa

revision = "0001_address_station_charger"
down_revision: Union[str, None] = "6ceff4e7f9ea"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None
def upgrade():
    op.create_table(
        "addresses",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("hno", sa.String(50), nullable=True),
        sa.Column("street_village", sa.String(255), nullable=False),
        sa.Column("city", sa.String(100), nullable=False),
        sa.Column("state", sa.String(100), nullable=False),
        sa.Column("pincode", sa.String(10), nullable=False),
        sa.Column("lat", sa.Float(), nullable=True),
        sa.Column("long", sa.Float(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_addresses_city", "addresses", ["city"])
    op.create_index("ix_addresses_pincode", "addresses", ["pincode"])
    op.create_table(
        "charging_stations",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("owner_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(150), nullable=False),
        sa.Column("address_id", sa.Integer(), sa.ForeignKey("addresses.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("description", sa.String(500), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_charging_stations_owner_id", "charging_stations", ["owner_id"])
    op.create_index("ix_charging_stations_address_id", "charging_stations", ["address_id"])
    op.create_table(
        "chargers",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("station_id", sa.Integer(), sa.ForeignKey("charging_stations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("charger_code", sa.String(80), nullable=False, unique=True),
        sa.Column("connector_type", sa.String(50), nullable=False),
        sa.Column("charging_type", sa.String(2), nullable=False),
        sa.Column("power_kw", sa.Numeric(8, 2), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("availability", sa.String(20), nullable=False),
        sa.Column("price_per_kwh", sa.Numeric(10, 2), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_chargers_station_id", "chargers", ["station_id"])
    op.create_index("ix_chargers_charger_code", "chargers", ["charger_code"])

def downgrade():
    op.drop_index("ix_chargers_charger_code", table_name="chargers")
    op.drop_index("ix_chargers_station_id", table_name="chargers")
    op.drop_table("chargers")
    op.drop_index("ix_charging_stations_address_id", table_name="charging_stations")
    op.drop_index("ix_charging_stations_owner_id", table_name="charging_stations")
    op.drop_table("charging_stations")
    op.drop_index("ix_addresses_pincode", table_name="addresses")
    op.drop_index("ix_addresses_city", table_name="addresses")
    op.drop_table("addresses")
