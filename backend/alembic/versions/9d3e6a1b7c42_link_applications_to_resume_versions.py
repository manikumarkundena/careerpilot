"""link job applications to generated resume versions

Revision ID: 9d3e6a1b7c42
Revises: 4c1a8e7d2f90
Create Date: 2026-10-23
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "9d3e6a1b7c42"
down_revision: Union[str, Sequence[str], None] = "4c1a8e7d2f90"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "job_applications",
        sa.Column("resume_version_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.create_foreign_key(
        "fk_job_applications_resume_version_id",
        "job_applications",
        "resume_versions",
        ["resume_version_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index(
        "ix_job_applications_resume_version_id",
        "job_applications",
        ["resume_version_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_job_applications_resume_version_id",
        table_name="job_applications",
    )
    op.drop_constraint(
        "fk_job_applications_resume_version_id",
        "job_applications",
        type_="foreignkey",
    )
    op.drop_column("job_applications", "resume_version_id")
