"""clean recommendations table

Revision ID: 1064562d12b0
Revises: 5a4a068ea932
Create Date: 2026-11-18
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "1064562d12b0"
down_revision: Union[str, Sequence[str], None] = "5a4a068ea932"

branch_labels = None
depends_on = None


def upgrade() -> None:

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
            nullable=False
        )
    )