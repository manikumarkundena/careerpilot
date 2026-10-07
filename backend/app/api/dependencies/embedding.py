from app.core.config import settings
from app.services.matching.embeddings import (
    EmbeddingProvider,
    OpenAICompatibleEmbeddingProvider,
)


def get_embedding_provider() -> EmbeddingProvider | None:
    """Return the configured semantic provider, or disable semantics cleanly."""
    if not settings.embedding_api_url:
        return None
    return OpenAICompatibleEmbeddingProvider()
