"""create fault detections table

Revision ID: 2868abcfca9b
Revises: e1473e836285
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "2868abcfca9b"
down_revision: Union[str, Sequence[str], None] = "e1473e836285"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:

    op.create_table(
        "fault_detections",

        sa.Column("id", sa.Integer(), primary_key=True),

        sa.Column("station_id", sa.Integer(), nullable=False),

        sa.Column("connector_id", sa.Integer(), nullable=False),

        sa.Column("fault_type", sa.String(), nullable=False),

        sa.Column("severity", sa.String(), nullable=False),

        sa.Column("confidence", sa.Float(), nullable=False),

        sa.Column(
            "detected_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
        ),
    )

    op.create_index(
        op.f("ix_fault_detections_id"),
        "fault_detections",
        ["id"],
        unique=False,
    )


def downgrade() -> None:

    op.drop_index(
        op.f("ix_fault_detections_id"),
        table_name="fault_detections",
    )

    op.drop_table("fault_detections")