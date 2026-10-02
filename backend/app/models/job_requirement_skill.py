import uuid
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base
from app.models.mixins import TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.models.job_requirement import JobRequirement
    from app.models.skill_catalog import SkillCatalog


class JobRequirementSkill(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "job_requirement_skills"

    requirement_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("job_requirements.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    skill_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("skill_catalog.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    requirement: Mapped["JobRequirement"] = relationship(
        back_populates="skills"
    )

    skill: Mapped["SkillCatalog"] = relationship()
