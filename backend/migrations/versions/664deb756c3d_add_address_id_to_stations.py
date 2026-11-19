"""add address id to stations

Revision ID: 664deb756c3d
Revises: 382cf182a0f9
Create Date: 2026-11-19 00:16:47.571268

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '664deb756c3d'
down_revision: Union[str, Sequence[str], None] = '382cf182a0f9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
