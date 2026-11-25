
"""add station owner

Revision ID: 042b1a0729ae
Revises: 4e63b0c1c200
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "042b1a0729ae"
down_revision: Union[str, Sequence[str], None] = "4e63b0c1c200"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "stations",
        sa.Column("owner_id", sa.Uuid(), nullable=True),
    )

    op.create_index(
        "ix_stations_owner_id",
        "stations",
        ["owner_id"],
        unique=False,
    )

    op.create_foreign_key(
        "fk_stations_owner_id_users",
        "stations",
        "users",
        ["owner_id"],
        ["id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    op.drop_constraint(
        "fk_stations_owner_id_users",
        "stations",
        type_="foreignkey",
    )

    op.drop_index(
        "ix_stations_owner_id",
        table_name="stations",
    )

    op.drop_column("stations", "owner_id")
