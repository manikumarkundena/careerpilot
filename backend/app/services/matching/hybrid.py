from __future__ import annotations

from dataclasses import dataclass

from app.services.matching.embeddings import cosine_similarity

@dataclass(frozen=True, slots=True)
class HybridWeights:
    skill: float = 0.45
    requirement: float = 0.35
    semantic: float = 0.20

    def __post_init__(self) -> None:
        values = (self.skill, self.requirement, self.semantic)
        if any(value < 0 for value in values):
            raise ValueError("Hybrid weights cannot be negative")
        if sum(values) <= 0:
            raise ValueError("At least one hybrid weight must be positive")

    @property
    def normalized(self) -> tuple[float, float, float]:
        total = self.skill + self.requirement + self.semantic
        return (self.skill / total, self.requirement / total, self.semantic / total)

def calculate_semantic_similarity(candidate_embedding: list[float], job_embedding: list[float]) -> float:
    similarity = cosine_similarity(candidate_embedding, job_embedding)
    return max(0.0, min(1.0, (similarity + 1.0) / 2.0))

def calculate_hybrid_score(*, skill_coverage: float, requirement_coverage: float, semantic_similarity: float | None = None, weights: HybridWeights | None = None) -> float:
    weights = weights or HybridWeights()
    skill_weight, requirement_weight, semantic_weight = weights.normalized
    skill = max(0.0, min(1.0, skill_coverage))
    requirement = max(0.0, min(1.0, requirement_coverage))
    if semantic_similarity is None:
        active_total = skill_weight + requirement_weight
        score = (skill * skill_weight + requirement * requirement_weight) / active_total
    else:
        semantic = max(0.0, min(1.0, semantic_similarity))
        score = skill * skill_weight + requirement * requirement_weight + semantic * semantic_weight
    return round(score * 100, 2)