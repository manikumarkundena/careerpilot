from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path

from app.services.matching.ranking_metrics import (
    mean_reciprocal_rank,
    ndcg_at_k,
    recall_at_k,
)


def load_relevance_judgments(path: str | Path) -> dict[str, dict[str, float]]:
    judgments: dict[str, dict[str, float]] = defaultdict(dict)
    with Path(path).open(encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            record = json.loads(line)
            relevance = float(record["relevance"])
            if relevance < 0 or relevance > 3:
                raise ValueError(f"Line {line_number}: relevance must be between 0 and 3")
            judgments[record["candidate_id"]][record["job_id"]] = relevance
    return dict(judgments)


def evaluate_ranked_results(
    ranked_job_ids_by_candidate: dict[str, list[str]],
    judgments: dict[str, dict[str, float]],
    *,
    k: int = 10,
) -> dict[str, float]:
    if k <= 0:
        raise ValueError("k must be positive")
    candidates = [candidate_id for candidate_id in ranked_job_ids_by_candidate if candidate_id in judgments]
    if not candidates:
        raise ValueError("No candidates overlap between results and judgments")

    recall_values = []
    mrr_values = []
    ndcg_values = []

    for candidate_id in candidates:
        ranked = ranked_job_ids_by_candidate[candidate_id]
        relevance = judgments[candidate_id]
        relevant = {job_id for job_id, score in relevance.items() if score > 0}
        recall_values.append(recall_at_k(ranked, relevant, k))
        mrr_values.append(mean_reciprocal_rank(ranked, relevant))
        ndcg_values.append(ndcg_at_k(ranked, relevance, k))

    count = len(candidates)
    return {
        "candidates_evaluated": float(count),
        "recall_at_k": sum(recall_values) / count,
        "mrr": sum(mrr_values) / count,
        "ndcg_at_k": sum(ndcg_values) / count,
    }
