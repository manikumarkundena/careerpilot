from __future__ import annotations

from dataclasses import dataclass, field

from app.services.resume.content_selector import ContentCandidate, select_relevant_content


@dataclass(slots=True)
class ResumeRepresentation:
    """Structured, factual intermediate representation for rendering."""

    headline: str | None
    summary: str | None
    skills: list[str] = field(default_factory=list)
    selected_content: list[ContentCandidate] = field(default_factory=list)


def build_resume_representation(
    profile,
    *,
    target_keywords: set[str] | None = None,
    content_limit: int = 12,
) -> ResumeRepresentation:
    target_keywords = target_keywords or set()
    candidates = []
    from app.services.resume.profile_adapter import build_profile_content_candidates

    candidates.extend(build_profile_content_candidates(profile))
    selected = select_relevant_content(
        candidates,
        target_keywords,
        limit=content_limit,
    )

    skills = [
        profile_skill.skill.name
        for profile_skill in profile.skills
        if profile_skill.skill is not None
    ]

    return ResumeRepresentation(
        headline=profile.headline,
        summary=profile.summary,
        skills=skills,
        selected_content=selected,
    )
