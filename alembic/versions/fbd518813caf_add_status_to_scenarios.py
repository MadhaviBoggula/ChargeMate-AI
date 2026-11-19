"""add status to scenarios

Revision ID: fbd518813caf
Revises: ba9d0e6efd8e
Create Date: 2026-11-19
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "fbd518813caf"
down_revision: Union[str, None] = "ba9d0e6efd8e"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "scenarios",
        sa.Column(
            "status",
            sa.String(length=50),
            nullable=False,
            server_default="Created"
        )
    )


def downgrade() -> None:
    op.drop_column(
        "scenarios",
        "status"
    )