from __future__ import annotations

import uuid

from sqlalchemy import Integer, String, UniqueConstraint
from sqlalchemy.types import UserDefinedType
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base
from app.models.mixins import TimestampMixin, UUIDMixin


class Vector1536(UserDefinedType):
    cache_ok = True

    def get_col_spec(self, **kwargs) -> str:
        return "VECTOR(1536)"

    def bind_processor(self, dialect):
        def process(value):
            if value is None:
                return None
            return "[" + ",".join(str(float(item)) for item in value) + "]"
        return process

    def result_processor(self, dialect, coltype):
        def process(value):
            if value is None:
                return None
            return [float(item) for item in value.strip("[]").split(",") if item]
        return process



class SemanticEmbedding(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "semantic_embeddings"

    entity_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )
    entity_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
    )
    model: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
    )
    dimension: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )
    source_hash: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
    )
    embedding: Mapped[list[float]] = mapped_column(
        Vector1536,
        nullable=False,
    )

    __table_args__ = (
        UniqueConstraint(
            "entity_type",
            "entity_id",
            "model",
            name="uq_semantic_embeddings_entity_model",
        ),
    )
