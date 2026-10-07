from __future__ import annotations

from math import log2


def recall_at_k(
    ranked_job_ids: list[str],
    relevant_job_ids: set[str],
    k: int,
) -> float:
    """Fraction of known relevant jobs retrieved in the top k."""
    if not relevant_job_ids:
        return 0.0
    if k <= 0:
        return 0.0

    retrieved = set(ranked_job_ids[:k])
    return len(retrieved & relevant_job_ids) / len(relevant_job_ids)


def mean_reciprocal_rank(
    ranked_job_ids: list[str],
    relevant_job_ids: set[str],
) -> float:
    """Reciprocal rank of the first relevant result."""
    if not relevant_job_ids:
        return 0.0

    for rank, job_id in enumerate(ranked_job_ids, start=1):
        if job_id in relevant_job_ids:
            return 1.0 / rank

    return 0.0


def ndcg_at_k(
    ranked_job_ids: list[str],
    relevance: dict[str, float],
    k: int,
) -> float:
    """Normalized discounted cumulative gain for graded relevance."""
    if k <= 0:
        return 0.0

    def dcg(ids: list[str]) -> float:
        return sum(
            (2.0 ** max(relevance.get(job_id, 0.0), 0.0) - 1.0)
            / log2(rank + 1)
            for rank, job_id in enumerate(ids, start=1)
        )

    actual = dcg(ranked_job_ids[:k])
    ideal_ids = sorted(
        relevance,
        key=lambda job_id: relevance[job_id],
        reverse=True,
    )
    ideal = dcg(ideal_ids[:k])

    if ideal == 0.0:
        return 0.0

    return actual / ideal
