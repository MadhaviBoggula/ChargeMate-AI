"""merge stations and RAG migrations

Revision ID: 4e63b0c1c200
Revises: 0002_rag_knowledge, 99a049eedf79
Create Date: 2026-11-14 20:47:51.674811

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '4e63b0c1c200'
down_revision: Union[str, Sequence[str], None] = ('0002_rag_knowledge', '99a049eedf79')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
