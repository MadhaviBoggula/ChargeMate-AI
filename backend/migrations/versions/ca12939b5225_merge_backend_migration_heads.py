"""merge backend migration heads

Revision ID: ca12939b5225
Revises: 8c964cfb67f3, c5f8e2a1b4d6
Create Date: 2026-11-24 17:14:00.792645

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ca12939b5225'
down_revision: Union[str, Sequence[str], None] = ('8c964cfb67f3', 'c5f8e2a1b4d6')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
