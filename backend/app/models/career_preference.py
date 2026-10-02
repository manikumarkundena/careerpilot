import uuid
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base
from app.models.mixins import TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.models.career_profile import CareerProfile


class CareerPreference(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "career_preferences"

    profile_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("career_profiles.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True,
    )

    target_roles: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    preferred_locations: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    remote_preference: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )

    employment_types: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    minimum_salary: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    currency: Mapped[str | None] = mapped_column(
        String(10),
        nullable=True,
    )

    willing_to_relocate: Mapped[bool | None] = mapped_column(
        Boolean,
        nullable=True,
    )

    preferred_experience_level: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    profile: Mapped["CareerProfile"] = relationship(
        back_populates="preferences",
    )
