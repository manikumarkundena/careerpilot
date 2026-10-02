from __future__ import annotations

import hashlib
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.semantic_embedding import SemanticEmbedding
from app.services.matching.embeddings import (
    EmbeddingError,
    EmbeddingProvider,
    validate_embedding,
)


def semantic_source_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


async def get_or_create_embedding(
    *,
    entity_type: str,
    entity_id: UUID,
    source_text: str,
    provider: EmbeddingProvider,
    session: AsyncSession,
    model: str | None = None,
    dimension: int | None = None,
) -> SemanticEmbedding:
    if not source_text.strip():
        raise EmbeddingError("Cannot persist an embedding for empty source text")

    model_name = model or settings.embedding_model
    expected_dimension = dimension or settings.embedding_dimension
    source_hash = semantic_source_hash(source_text)

    result = await session.execute(
        select(SemanticEmbedding).where(
            SemanticEmbedding.entity_type == entity_type,
            SemanticEmbedding.entity_id == entity_id,
            SemanticEmbedding.model == model_name,
        )
    )
    existing = result.scalar_one_or_none()

    if (
        existing is not None
        and existing.source_hash == source_hash
        and existing.dimension == expected_dimension
    ):
        return existing

    vector = await provider.embed(source_text)
    vector = validate_embedding(
        vector,
        expected_dimension=expected_dimension,
    )

    if existing is None:
        existing = SemanticEmbedding(
            entity_type=entity_type,
            entity_id=entity_id,
            model=model_name,
            dimension=expected_dimension,
            source_hash=source_hash,
            embedding=vector,
        )
        session.add(existing)
    else:
        existing.dimension = expected_dimension
        existing.source_hash = source_hash
        existing.embedding = vector

    await session.flush()
    return existing
