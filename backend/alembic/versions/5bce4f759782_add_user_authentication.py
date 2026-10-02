"""add user authentication

Revision ID: 5bce4f759782
Revises: fa6cb9fab1b8
Create Date: 2026-10-02 10:08:23.980307

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "5bce4f759782"
down_revision: Union[str, Sequence[str], None] = "fa6cb9fab1b8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""

    op.add_column(
        "users",
        sa.Column(
            "password_hash",
            sa.String(length=255),
            nullable=True,
        ),
    )

    # Existing development users do not have passwords yet.
    # Give them a deliberately unusable value so they cannot
    # authenticate until a password is established.
    op.execute(
        """
        UPDATE users
        SET password_hash = '!'
        WHERE password_hash IS NULL
        """
    )

    op.alter_column(
        "users",
        "password_hash",
        existing_type=sa.String(length=255),
        nullable=False,
    )


def downgrade() -> None:
    """Downgrade schema."""

    op.drop_column("users", "password_hash")