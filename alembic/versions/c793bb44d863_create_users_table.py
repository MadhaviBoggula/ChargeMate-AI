"""create users table

Revision ID: c793bb44d863
Revises: ba9d0e6efd8e
Create Date: 2026-11-12

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "c793bb44d863"
down_revision: Union[str, Sequence[str], None] = "ba9d0e6efd8e"
branch_labels = None
depends_on = None


def upgrade() -> None:

    op.create_table(
        "users",

        sa.Column(
            "id",
            sa.Integer(),
            primary_key=True,
            nullable=False
        ),

        sa.Column(
            "full_name",
            sa.String(length=100),
            nullable=False
        ),

        sa.Column(
            "email",
            sa.String(length=255),
            nullable=False,
            unique=True
        ),

        sa.Column(
            "password",
            sa.String(length=255),
            nullable=False
        ),

        sa.Column(
            "role",
            sa.String(length=50),
            nullable=False
        ),

        sa.Column(
            "created_at",
            sa.DateTime(),
            server_default=sa.func.now(),
            nullable=False
        )
    )


def downgrade() -> None:

    op.drop_table("users")