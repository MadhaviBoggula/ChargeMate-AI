"""create favorite stations table

Revision ID: cd8df20f5842
Revises: 54b3727bf95f
Create Date: 2026-11-18 05:26:18.889824

"""

from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "cd8df20f5842"
down_revision: Union[str, Sequence[str], None] = "54b3727bf95f"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""

    op.create_foreign_key(
        "fk_favorite_stations_station_id",
        "favorite_stations",
        "stations",
        ["station_id"],
        ["id"]
    )


def downgrade() -> None:
    """Downgrade schema."""

    op.drop_constraint(
        "fk_favorite_stations_station_id",
        "favorite_stations",
        type_="foreignkey"
    )