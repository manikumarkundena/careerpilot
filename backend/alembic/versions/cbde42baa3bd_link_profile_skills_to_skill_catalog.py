"""link profile skills to skill catalog

Revision ID: cbde42baa3bd
Revises: e40be46c0f04
Create Date: 2026-09-17 18:08:36.466718

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "cbde42baa3bd"
down_revision: Union[str, Sequence[str], None] = "e40be46c0f04"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""

    op.add_column(
        "skills",
        sa.Column("skill_id", sa.UUID(), nullable=False),
    )

    op.create_index(
        op.f("ix_skills_skill_id"),
        "skills",
        ["skill_id"],
        unique=False,
    )

    op.create_foreign_key(
        "fk_skills_skill_id_skill_catalog",
        "skills",
        "skill_catalog",
        ["skill_id"],
        ["id"],
        ondelete="RESTRICT",
    )

    op.drop_column("skills", "name")
    op.drop_column("skills", "category")


def downgrade() -> None:
    """Downgrade schema."""

    op.add_column(
        "skills",
        sa.Column(
            "name",
            sa.VARCHAR(length=150),
            nullable=False,
        ),
    )

    op.add_column(
        "skills",
        sa.Column(
            "category",
            sa.VARCHAR(length=100),
            nullable=True,
        ),
    )

    op.drop_constraint(
        "fk_skills_skill_id_skill_catalog",
        "skills",
        type_="foreignkey",
    )

    op.drop_index(
        op.f("ix_skills_skill_id"),
        table_name="skills",
    )

    op.drop_column("skills", "skill_id")