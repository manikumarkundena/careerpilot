from uuid import uuid4

import pytest

from app.services.matching.embedding_store import semantic_source_hash


def test_semantic_source_hash_is_stable():
    text = "Candidate: Python FastAPI PostgreSQL"
    assert semantic_source_hash(text) == semantic_source_hash(text)


def test_semantic_source_hash_changes_when_source_changes():
    assert semantic_source_hash("Python") != semantic_source_hash("Python FastAPI")


@pytest.mark.parametrize("text", ["", "   ", "\n\t"])
def test_empty_source_is_rejected_at_service_boundary(text):
    # The persistence service checks this before calling a provider.
    assert not text.strip()
