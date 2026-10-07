from __future__ import annotations

from dataclasses import dataclass

from app.services.resume.content_selector import ContentCandidate, select_relevant_content
from app.services.resume.job_gap import ResumeGapAnalysis


@dataclass(slots=True, frozen=True)
class ResumeOptimization:
    selected_content: tuple[ContentCandidate, ...]
    prioritized_skills: tuple[str, ...]
    covered_keywords: tuple[str, ...]
    uncovered_keywords: tuple[str, ...]


def optimize_resume_for_job(
    *,
    candidates: list[ContentCandidate],
    candidate_skills: list[str],
    target_keywords: set[str],
    gap_analysis: ResumeGapAnalysis | None = None,
    content_limit: int = 8,
) -> ResumeOptimization:
    """Prioritize existing facts for a target job.

    This layer changes ordering and selection only. It never rewrites source
    text or adds skills that are absent from the candidate profile.
    """
    # Preserve the original keyword spelling for output while using normalized
    # values exclusively for case-insensitive matching.
    target_by_normalized = {
        keyword.strip().lower(): keyword.strip()
        for keyword in target_keywords
        if keyword.strip()
    }
    normalized_targets = set(target_by_normalized)

    selected = select_relevant_content(
        candidates,
        normalized_targets,
        limit=content_limit,
    )

    skill_by_normalized = {
        skill.strip().lower(): skill
        for skill in candidate_skills
        if skill.strip()
    }

    prioritized_skills = tuple(
        skill_by_normalized[keyword]
        for keyword in sorted(normalized_targets)
        if keyword in skill_by_normalized
    )

    covered_normalized = {
        skill.strip().lower()
        for skill in prioritized_skills
    }
    covered_keywords = tuple(
        target_by_normalized[keyword]
        for keyword in sorted(normalized_targets)
        if keyword in covered_normalized
    )
    uncovered_keywords = tuple(
        target_by_normalized[keyword]
        for keyword in sorted(normalized_targets)
        if keyword not in covered_normalized
    )

    # gap_analysis remains an optional integration point for the next layer.
    return ResumeOptimization(
        selected_content=tuple(selected),
        prioritized_skills=prioritized_skills,
        covered_keywords=covered_keywords,
        uncovered_keywords=uncovered_keywords,
    )
