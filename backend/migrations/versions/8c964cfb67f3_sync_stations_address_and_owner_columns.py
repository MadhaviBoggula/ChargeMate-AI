"""sync stations address and owner columns

Revision ID: 8c964cfb67f3
Revises: 664deb756c3d
Create Date: 2026-11-19 14:15:33.107643

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '8c964cfb67f3'
down_revision: Union[str, Sequence[str], None] = '664deb756c3d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None
def upgrade():
    op.add_column(
        "stations",
        sa.Column(
            "address_id",
            sa.Integer(),
            nullable=True,
        ),
    )

    op.add_column(
        "stations",
        sa.Column(
            "owner_id",
            postgresql.UUID(as_uuid=True),
            nullable=True,
        ),
    )


def downgrade():
    op.drop_column("stations", "owner_id")
    op.drop_column("stations", "address_id")

    # ### end Alembic commands ###
