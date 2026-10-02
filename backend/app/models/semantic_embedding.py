from __future__ import annotations

import uuid

from sqlalchemy import Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base
from app.models.mixins import TimestampMixin, UUIDMixin


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
    # Stored as pgvector text representation for this first persistence step.
    # The next vector-search step will use the native VECTOR column/operator.
    embedding: Mapped[str] = mapped_column(
        Text,
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
