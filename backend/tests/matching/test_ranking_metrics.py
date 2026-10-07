import pytest

from app.services.matching.ranking_metrics import (
    mean_reciprocal_rank,
    ndcg_at_k,
    recall_at_k,
)


def test_recall_at_k_counts_relevant_results():
    ranked = ["a", "b", "c", "d"]
    relevant = {"b", "d"}

    assert recall_at_k(ranked, relevant, 3) == pytest.approx(0.5)
    assert recall_at_k(ranked, relevant, 4) == pytest.approx(1.0)


def test_recall_at_k_handles_empty_ground_truth():
    assert recall_at_k(["a", "b"], set(), 2) == 0.0
    assert recall_at_k(["a", "b"], {"a"}, 0) == 0.0


def test_mean_reciprocal_rank_uses_first_relevant_result():
    assert mean_reciprocal_rank(
        ["a", "b", "c"],
        {"b", "c"},
    ) == pytest.approx(0.5)

    assert mean_reciprocal_rank(
        ["a", "b"],
        {"x"},
    ) == 0.0


def test_ndcg_at_k_rewards_higher_relevance_earlier():
    relevance = {
        "a": 3.0,
        "b": 2.0,
        "c": 0.0,
    }

    ideal = ndcg_at_k(["a", "b", "c"], relevance, 3)
    worse = ndcg_at_k(["c", "b", "a"], relevance, 3)

    assert ideal == pytest.approx(1.0)
    assert 0.0 <= worse < ideal


def test_ndcg_at_k_handles_no_relevant_items():
    assert ndcg_at_k(["a", "b"], {"a": 0.0, "b": 0.0}, 2) == 0.0
