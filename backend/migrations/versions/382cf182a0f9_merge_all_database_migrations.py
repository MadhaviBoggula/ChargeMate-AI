"""merge all database migrations

Revision ID: 382cf182a0f9
Revises: fea351d7225d
Create Date: 2026-11-18 00:51:54.401869

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '382cf182a0f9'
down_revision: Union[str, Sequence[str], None] = 'fea351d7225d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
