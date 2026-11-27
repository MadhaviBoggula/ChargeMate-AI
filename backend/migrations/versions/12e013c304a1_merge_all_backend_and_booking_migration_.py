"""merge all backend and booking migration heads

Revision ID: 12e013c304a1
Revises: 1cf40d1107a9, ca12939b5225
Create Date: 2026-11-26 17:00:21.228564

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '12e013c304a1'
down_revision: Union[str, Sequence[str], None] = ('1cf40d1107a9', 'ca12939b5225')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
