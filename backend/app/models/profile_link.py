import uuid
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base
from app.models.mixins import TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.models.career_profile import CareerProfile


class ProfileLink(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "profile_links"

    profile_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("career_profiles.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    platform: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    label: Mapped[str | None] = mapped_column(
        String(150),
        nullable=True,
    )

    url: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
    )

    profile: Mapped["CareerProfile"] = relationship(
        back_populates="links",
    )

