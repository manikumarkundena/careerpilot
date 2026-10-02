import uuid
from typing import TYPE_CHECKING

from sqlalchemy import Float, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base
from app.models.mixins import TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.models.job import Job
    from app.models.skill_catalog import SkillCatalog
    from app.models.job_requirement_skill import JobRequirementSkil


class JobRequirement(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "job_requirements"

    job_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("jobs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    requirement_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    text: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )


    importance: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    evidence: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    job: Mapped["Job"] = relationship(
        back_populates="requirements",
    )

    skills: Mapped[list["JobRequirementSkill"]] = relationship(
        back_populates="requirement",
        cascade="all, delete-orphan",
    )