from __future__ import annotations

import math
from collections.abc import Sequence
from typing import Protocol

import httpx

from app.core.config import settings


class EmbeddingProvider(Protocol):
    async def embed(self, text: str) -> list[float]:
        ...


class EmbeddingError(RuntimeError):
    """Raised when an embedding cannot be generated or validated."""


class OpenAICompatibleEmbeddingProvider:
    """Small provider adapter for OpenAI-compatible /embeddings APIs."""

    def __init__(
        self,
        *,
        api_url: str | None = None,
        api_key: str | None = None,
        model: str | None = None,
        dimension: int | None = None,
        timeout_seconds: float | None = None,
    ) -> None:
        self.api_url = api_url or settings.embedding_api_url
        self.api_key = api_key or settings.embedding_api_key
        self.model = model or settings.embedding_model
        self.dimension = dimension or settings.embedding_dimension
        self.timeout_seconds = timeout_seconds or settings.embedding_timeout_seconds

    async def embed(self, text: str) -> list[float]:
        if not self.api_url:
            raise EmbeddingError("Embedding API URL is not configured")

        if not text.strip():
            raise EmbeddingError("Cannot embed empty text")

        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        payload = {"input": text, "model": self.model}

        try:
            async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
                response = await client.post(
                    self.api_url,
                    json=payload,
                    headers=headers,
                )
                response.raise_for_status()
                body = response.json()
        except (httpx.HTTPError, ValueError) as exc:
            raise EmbeddingError("Embedding provider request failed") from exc

        try:
            vector = body["data"][0]["embedding"]
        except (KeyError, IndexError, TypeError) as exc:
            raise EmbeddingError("Embedding provider returned an invalid response") from exc

        return validate_embedding(vector, expected_dimension=self.dimension)


def validate_embedding(
    vector: Sequence[float],
    *,
    expected_dimension: int,
) -> list[float]:
    if len(vector) != expected_dimension:
        raise EmbeddingError(
            f"Expected embedding dimension {expected_dimension}, got {len(vector)}"
        )

    normalized: list[float] = []
    for value in vector:
        try:
            numeric = float(value)
        except (TypeError, ValueError) as exc:
            raise EmbeddingError("Embedding contains a non-numeric value") from exc

        if not math.isfinite(numeric):
            raise EmbeddingError("Embedding contains a non-finite value")

        normalized.append(numeric)

    return normalized


def cosine_similarity(
    left: Sequence[float],
    right: Sequence[float],
) -> float:
    if len(left) != len(right):
        raise ValueError("Embedding dimensions must match")

    left_norm = math.sqrt(sum(value * value for value in left))
    right_norm = math.sqrt(sum(value * value for value in right))

    if left_norm == 0.0 or right_norm == 0.0:
        return 0.0

    dot = sum(a * b for a, b in zip(left, right))
    return dot / (left_norm * right_norm)
