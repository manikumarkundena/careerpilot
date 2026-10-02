import uuid
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base
from app.models.mixins import TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.models.career_profile import CareerProfile
    from app.models.skill_catalog import SkillCatalog


class Skill(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "skills"

    profile_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("career_profiles.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    skill_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("skill_catalog.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    proficiency: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )

    profile: Mapped["CareerProfile"] = relationship(
        back_populates="skills",
    )

    skill: Mapped["SkillCatalog"] = relationship(
        back_populates="profile_skills",
    )