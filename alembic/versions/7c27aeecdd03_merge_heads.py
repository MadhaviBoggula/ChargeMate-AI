"""merge heads

Revision ID: 7c27aeecdd03
Revises: 1064562d12b0, fbd518813caf
Create Date: 2026-11-19 13:35:09.946759

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7c27aeecdd03'
down_revision: Union[str, Sequence[str], None] = ('1064562d12b0', 'fbd518813caf')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
