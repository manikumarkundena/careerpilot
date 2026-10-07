from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True, frozen=True)
class ResumeGap:
    requirement: str
    importance: float
    matched: bool
    matched_skills: tuple[str, ...] = ()


@dataclass(slots=True, frozen=True)
class ResumeGapAnalysis:
    gaps: tuple[ResumeGap, ...]
    matched_requirements: tuple[ResumeGap, ...]
    keyword_coverage: float


def analyze_job_requirements(
    requirements,
    candidate_skill_names: set[str],
) -> ResumeGapAnalysis:
    """Analyze a job against known candidate skills.

    This is deliberately deterministic and factual. A missing skill is a gap;
    it is never converted into a claim that the candidate possesses it.
    """
    normalized = {name.strip().lower() for name in candidate_skill_names if name.strip()}
    gaps: list[ResumeGap] = []
    matched: list[ResumeGap] = []

    for requirement in requirements:
        requirement_skills = [
            skill.skill.name
            for skill in requirement.skills
            if getattr(skill, "skill", None) is not None
        ]
        matched_skills = tuple(
            name for name in requirement_skills
            if name.strip().lower() in normalized
        )
        is_matched = bool(matched_skills)
        item = ResumeGap(
            requirement=requirement.text,
            importance=float(requirement.importance or 0.0),
            matched=is_matched,
            matched_skills=matched_skills,
        )
        (matched if is_matched else gaps).append(item)

    total = len(requirements)
    coverage = len(matched) / total if total else 1.0
    return ResumeGapAnalysis(
        gaps=tuple(gaps),
        matched_requirements=tuple(matched),
        keyword_coverage=coverage,
    )
