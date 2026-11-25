
"""add booking duration fields

Revision ID: 1cf40d1107a9
Revises: c642fc8a5bb5
Create Date: 2026-11-24 18:04:06.450843
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "1cf40d1107a9"
down_revision: Union[str, Sequence[str], None] = "c642fc8a5bb5"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add reservation duration and end time."""

    op.add_column(
        "bookings",
        sa.Column(
            "duration_minutes",
            sa.Integer(),
            nullable=False,
        ),
    )

    op.add_column(
        "bookings",
        sa.Column(
            "end_time",
            sa.DateTime(timezone=True),
            nullable=False,
        ),
    )

    op.create_check_constraint(
        "ck_bookings_duration_minutes_allowed",
        "bookings",
        "duration_minutes IN (30, 60, 120)",
    )

    op.create_check_constraint(
        "ck_bookings_end_time_after_booking_time",
        "bookings",
        "end_time > booking_time",
    )


def downgrade() -> None:
    """Remove reservation duration and end time."""

    op.drop_constraint(
        "ck_bookings_end_time_after_booking_time",
        "bookings",
        type_="check",
    )

    op.drop_constraint(
        "ck_bookings_duration_minutes_allowed",
        "bookings",
        type_="check",
    )

    op.drop_column("bookings", "end_time")
    op.drop_column("bookings", "duration_minutes")
