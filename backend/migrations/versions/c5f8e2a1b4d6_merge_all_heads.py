"""merge address/charger and stations/RAG heads

Revision ID: c5f8e2a1b4d6
Revises: 4e63b0c1c200, 0001_address_station_charger
Create Date: 2026-11-20 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c5f8e2a1b4d6'
down_revision: Union[str, Sequence[str], None] = ('4e63b0c1c200', '0001_address_station_charger')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
