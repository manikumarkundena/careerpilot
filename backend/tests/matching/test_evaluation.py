import json

import pytest

from app.services.matching.evaluation import (
    evaluate_ranked_results,
    load_relevance_judgments,
)


def test_load_relevance_judgments(tmp_path):
    path = tmp_path / "judgments.jsonl"
    path.write_text(
        json.dumps({
            "candidate_id": "candidate-1",
            "job_id": "job-1",
            "relevance": 3,
            "label_source": "human_review",
        }) + "\n",
        encoding="utf-8",
    )
    assert load_relevance_judgments(path) == {"candidate-1": {"job-1": 3.0}}


def test_load_relevance_judgments_rejects_invalid_relevance(tmp_path):
    path = tmp_path / "judgments.jsonl"
    path.write_text('{"candidate_id":"c","job_id":"j","relevance":4}\n', encoding="utf-8")
    with pytest.raises(ValueError, match="between 0 and 3"):
        load_relevance_judgments(path)


def test_evaluate_ranked_results():
    result = evaluate_ranked_results(
        {"candidate-1": ["job-2", "job-1", "job-3"]},
        {"candidate-1": {"job-1": 3.0, "job-2": 0.0, "job-3": 1.0}},
        k=2,
    )
    assert result["candidates_evaluated"] == 1.0
    assert result["recall_at_k"] == pytest.approx(0.5)
    assert result["mrr"] == pytest.approx(0.5)
    assert 0.0 < result["ndcg_at_k"] < 1.0


def test_evaluate_ranked_results_requires_overlap():
    with pytest.raises(ValueError, match="No candidates overlap"):
        evaluate_ranked_results({"candidate-1": ["job-1"]}, {"candidate-2": {"job-1": 3.0}})
