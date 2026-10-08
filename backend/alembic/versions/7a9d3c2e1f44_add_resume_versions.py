"""add persistent resume versions

Revision ID: 7a9d3c2e1f44
Revises: 2f4c9b7d1e33
Create Date: 2026-10-08 15:10:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "7a9d3c2e1f44"
down_revision: Union[str, Sequence[str], None] = "2f4c9b7d1e33"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "resume_versions",
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
        sa.Column(
            "profile_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),
        sa.Column(
            "target_job_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column(
            "template_version",
            sa.String(length=50),
            nullable=False,
            server_default="1",
        ),
        sa.Column("document_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("quality_report_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("pdf_bytes", sa.LargeBinary(), nullable=False),
        sa.Column("pdf_sha256", sa.String(length=64), nullable=False),
        sa.Column(
            "generated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["profile_id"],
            ["career_profiles.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["target_job_id"],
            ["jobs.id"],
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "profile_id",
            "version",
            name="uq_resume_versions_profile_version",
        ),
    )
    op.create_index(
        "ix_resume_versions_profile_id",
        "resume_versions",
        ["profile_id"],
        unique=False,
    )
    op.create_index(
        "ix_resume_versions_target_job_id",
        "resume_versions",
        ["target_job_id"],
        unique=False,
    )
    op.create_index(
        "ix_resume_versions_pdf_sha256",
        "resume_versions",
        ["pdf_sha256"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_resume_versions_pdf_sha256", table_name="resume_versions")
    op.drop_index("ix_resume_versions_target_job_id", table_name="resume_versions")
    op.drop_index("ix_resume_versions_profile_id", table_name="resume_versions")
    op.drop_table("resume_versions")
