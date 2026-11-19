"""create demand forecasts table

Revision ID: e1473e836285
Revises: cd8df20f5842
Create Date: 2026-11-18

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "e1473e836285"
down_revision: Union[str, Sequence[str], None] = "cd8df20f5842"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:

    op.create_table(
        "demand_forecasts",

        sa.Column("id", sa.Integer(), primary_key=True),

        sa.Column("station_id", sa.Integer(), nullable=False),

        sa.Column("forecast_date", sa.String(), nullable=False),

        sa.Column("predicted_demand", sa.Float(), nullable=False),

        sa.Column("demand_level", sa.String(), nullable=False),

        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now()
        ),
    )

    op.create_index(
        op.f("ix_demand_forecasts_id"),
        "demand_forecasts",
        ["id"],
        unique=False,
    )


def downgrade() -> None:

    op.drop_index(
        op.f("ix_demand_forecasts_id"),
        table_name="demand_forecasts",
    )

    op.drop_table("demand_forecasts")