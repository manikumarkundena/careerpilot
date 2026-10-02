import uuid
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base
from app.models.mixins import TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.models.education import Education
    from app.models.user import User
    from app.models.experience import Experience
    from app.models.skill import Skill
    from app.models.project import Project
    from app.models.certification import Certification
    from app.models.achievement import Achievement
    from app.models.profile_link import ProfileLink
    from app.models.career_preference import CareerPreference


class CareerProfile(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "career_profiles"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True,
    )

    headline: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    summary: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    target_roles: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    user: Mapped["User"] = relationship(
        back_populates="career_profile",
    )

    education: Mapped[list["Education"]] = relationship(
        back_populates="profile",
        cascade="all, delete-orphan",
        order_by="Education.start_date",
    )

    experience: Mapped[list["Experience"]] = relationship(
    back_populates="profile",
    cascade="all, delete-orphan",
    order_by="Experience.start_date",
    )

    skills: Mapped[list["Skill"]] = relationship(
    back_populates="profile",
    cascade="all, delete-orphan",
    )

    projects: Mapped[list["Project"]] = relationship(
    back_populates="profile",
    cascade="all, delete-orphan",
    order_by="Project.start_date",
    )

    certifications: Mapped[list["Certification"]] = relationship(
    back_populates="profile",
    cascade="all, delete-orphan",
    order_by="Certification.issue_date",
    )

    achievements: Mapped[list["Achievement"]] = relationship(
    back_populates="profile",
    cascade="all, delete-orphan",
    order_by="Achievement.achievement_date",
    )

    links: Mapped[list["ProfileLink"]] = relationship(
    back_populates="profile",
    cascade="all, delete-orphan",
    )

    preferences: Mapped["CareerPreference | None"] = relationship(
    back_populates="profile",
    uselist=False,
    cascade="all, delete-orphan",
    )