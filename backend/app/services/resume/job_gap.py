from __future__ import annotations

from dataclasses import dataclass

from app.services.resume.jd_intelligence import (
    candidate_keyword_coverage,
    candidate_skill_matches_requirement_text,
)


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
    must_have_coverage: float = 1.0
    preferred_coverage: float = 1.0


def analyze_job_requirements(
    requirements,
    candidate_skill_names: set[str],
) -> ResumeGapAnalysis:
    """Analyze structured requirements plus their raw JD text.

    Candidate evidence remains limited to skills already present in the
    profile. Raw job text can improve matching, but can never create a claim.
    """
    normalized = {
        name.strip().lower(): name.strip()
        for name in candidate_skill_names
        if name.strip()
    }
    gaps: list[ResumeGap] = []
    matched: list[ResumeGap] = []

    for requirement in requirements:
        requirement_skills = [
            skill.skill.name
            for skill in requirement.skills
            if getattr(skill, "skill", None) is not None
        ]
        linked_matches = [
            name for name in requirement_skills
            if name.strip().lower() in normalized
        ]
        text_matches = candidate_skill_matches_requirement_text(
            requirement.text,
            candidate_skill_names,
        )
        matched_skills = tuple(dict.fromkeys((*linked_matches, *text_matches)))
        is_matched = bool(matched_skills)

        item = ResumeGap(
            requirement=requirement.text,
            importance=float(requirement.importance or 0.0),
            matched=is_matched,
            matched_skills=matched_skills,
        )
        (matched if is_matched else gaps).append(item)

    overall, must_have, preferred = candidate_keyword_coverage(
        requirements,
        candidate_skill_names,
    )
    return ResumeGapAnalysis(
        gaps=tuple(gaps),
        matched_requirements=tuple(matched),
        keyword_coverage=overall,
        must_have_coverage=must_have,
        preferred_coverage=preferred,
    )
