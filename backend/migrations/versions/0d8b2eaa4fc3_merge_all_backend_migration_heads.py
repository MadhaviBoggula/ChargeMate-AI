"""merge all backend migration heads

Revision ID: 0d8b2eaa4fc3
Revises: 12e013c304a1
Create Date: 2026-11-26 17:00:34.690066

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0d8b2eaa4fc3'
down_revision: Union[str, Sequence[str], None] = '12e013c304a1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
