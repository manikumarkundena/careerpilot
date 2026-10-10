"""add persisted job applications

Revision ID: 4c1a8e7d2f90
Revises: 7a9d3c2e1f44
Create Date: 2026-10-11
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "4c1a8e7d2f90"
down_revision: Union[str, Sequence[str], None] = "7a9d3c2e1f44"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "job_applications",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("job_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "status",
            sa.String(length=20),
            server_default="saved",
            nullable=False,
        ),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("applied_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["job_id"], ["jobs.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "user_id",
            "job_id",
            name="uq_job_applications_user_job",
        ),
    )
    op.create_index(
        "ix_job_applications_user_id",
        "job_applications",
        ["user_id"],
        unique=False,
    )
    op.create_index(
        "ix_job_applications_job_id",
        "job_applications",
        ["job_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_job_applications_job_id", table_name="job_applications")
    op.drop_index("ix_job_applications_user_id", table_name="job_applications")
    op.drop_table("job_applications")
