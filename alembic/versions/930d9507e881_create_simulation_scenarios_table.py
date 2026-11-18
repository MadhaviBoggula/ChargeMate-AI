"""create simulation scenarios table

Revision ID: 930d9507e881
Revises: 2868abcfca9b
Create Date: 2026-11-18
"""

from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "930d9507e881"
down_revision: Union[str, Sequence[str], None] = "2868abcfca9b"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Scenario table already exists in database.
    Skipping creation to sync Alembic revision.
    """
    pass


def downgrade() -> None:
    """
    Keep existing scenario table.
    """
    pass