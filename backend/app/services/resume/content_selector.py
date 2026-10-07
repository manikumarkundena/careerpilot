from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True, frozen=True)
class ContentCandidate:
    text: str
    source_type: str
    source_id: str
    keywords: tuple[str, ...] = ()
    priority: float = 0.0


def select_relevant_content(
    candidates: list[ContentCandidate],
    target_keywords: set[str],
    *,
    limit: int | None = None,
) -> list[ContentCandidate]:
    """Rank existing candidate facts without inventing new content.

    Matching is intentionally deterministic. Later LLM/ML components can
    improve prioritization while this layer remains the factual boundary.
    """
    normalized = {keyword.strip().lower() for keyword in target_keywords if keyword.strip()}

    def score(candidate: ContentCandidate) -> tuple[float, str]:
        overlap = sum(
            1 for keyword in candidate.keywords
            if keyword.strip().lower() in normalized
        )
        return (candidate.priority + overlap, candidate.text.lower())

    ranked = sorted(candidates, key=score, reverse=True)
    return ranked if limit is None else ranked[:limit]
