from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, LargeBinary, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base
from app.models.mixins import TimestampMixin, UUIDMixin


class ResumeVersion(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "resume_versions"
    __table_args__ = (
        UniqueConstraint(
            "profile_id",
            "version",
            name="uq_resume_versions_profile_version",
        ),
    )

    profile_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("career_profiles.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    target_job_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("jobs.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    version: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )
    template_version: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="1",
    )
    document_json: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
    )
    quality_report_json: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
    )
    pdf_bytes: Mapped[bytes] = mapped_column(
        LargeBinary,
        nullable=False,
    )
    pdf_sha256: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        index=True,
    )
    generated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    profile = relationship("CareerProfile")
    target_job = relationship("Job")
