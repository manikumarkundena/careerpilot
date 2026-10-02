from typing import TYPE_CHECKING

from sqlalchemy import Boolean, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base
from app.models.mixins import TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.models.skill import Skill
    from app.models.skill_alias import SkillAlias


class SkillCatalog(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "skill_catalog"

    name: Mapped[str] = mapped_column(
        String(150),
        unique=True,
        nullable=False,
        index=True,
    )

    category: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )

    aliases: Mapped[list["SkillAlias"]] = relationship(
        back_populates="skill",
        cascade="all, delete-orphan",
    )

    profile_skills: Mapped[list["Skill"]] = relationship(
        back_populates="skill",
    )