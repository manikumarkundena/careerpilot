import pytest

from app.services.matching.embeddings import (
    EmbeddingError,
    cosine_similarity,
    validate_embedding,
)


def test_validate_embedding_accepts_numeric_values():
    assert validate_embedding([1, 2.5, 3], expected_dimension=3) == [
        1.0,
        2.5,
        3.0,
    ]


def test_validate_embedding_rejects_wrong_dimension():
    with pytest.raises(EmbeddingError, match="Expected embedding dimension"):
        validate_embedding([1, 2], expected_dimension=3)


def test_validate_embedding_rejects_non_finite_values():
    with pytest.raises(EmbeddingError, match="non-finite"):
        validate_embedding([1, float("nan")], expected_dimension=2)


def test_cosine_similarity_identical_vectors_is_one():
    assert cosine_similarity([1.0, 0.0], [1.0, 0.0]) == pytest.approx(1.0)


def test_cosine_similarity_orthogonal_vectors_is_zero():
    assert cosine_similarity([1.0, 0.0], [0.0, 1.0]) == pytest.approx(0.0)


def test_cosine_similarity_rejects_dimension_mismatch():
    with pytest.raises(ValueError, match="dimensions"):
        cosine_similarity([1.0], [1.0, 2.0])


def test_cosine_similarity_handles_zero_vector():
    assert cosine_similarity([0.0, 0.0], [1.0, 0.0]) == 0.0
