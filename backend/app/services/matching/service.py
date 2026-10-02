from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.services.matching.candidate_loader import (
    load_candidate_snapshot,
)
from app.services.matching.job_loader import (
    load_job_snapshot,
)
from app.services.matching.models import MatchResult
from app.services.matching.requirement_matcher import (
    match_requirement,
)
from app.services.matching.skill_matcher import match_skills


def calculate_skill_coverage(
    candidate_skills,
    required_skills,
) -> float:
    if not required_skills:
        return 1.0

    normalized_candidate = {
        skill.strip().lower()
        for skill in candidate_skills
    }

    matched = sum(
        1
        for skill in required_skills
        if skill.strip().lower() in normalized_candidate
    )

    return matched / len(required_skills)


def calculate_requirement_coverage(
    requirements,
) -> float:
    if not requirements:
        return 1.0

    total_weight = sum(
        max(requirement.importance, 0.0)
        for requirement in requirements
    )

    if total_weight == 0:
        return 0.0

    matched_weight = sum(
        max(requirement.importance, 0.0)
        for requirement in requirements
        if requirement.matched
    )

    return matched_weight / total_weight


def match_candidate_to_job(
    *,
    candidate_skills: dict[str, str | None],
    required_skills: list[str],
    requirements: list[dict],
) -> MatchResult:
    skill_matches, missing_skills = match_skills(
        candidate_skills,
        required_skills,
    )

    requirement_matches = []

    for requirement in requirements:
        requirement_matches.append(
            match_requirement(
                requirement_type=requirement["requirement_type"],
                requirement_text=requirement["text"],
                importance=requirement.get("importance"),
                required_skills=requirement.get("skills", []),
                candidate_skills=candidate_skills,
            )
        )

    skill_coverage = calculate_skill_coverage(
        candidate_skills,
        required_skills,
    )

    requirement_coverage = calculate_requirement_coverage(
        requirement_matches
    )

    gaps = [
        f"Missing skill: {skill}"
        for skill in missing_skills
    ]

    return MatchResult(
        skill_coverage=round(skill_coverage, 4),
        requirement_coverage=round(
            requirement_coverage,
            4,
        ),
        matched_skills=[
            match.skill_name
            for match in skill_matches
            if match.matched
        ],
        missing_skills=missing_skills,
        matched_requirements=requirement_matches,
        gaps=gaps,
    )


async def match_candidate_to_job_from_db(
    *,
    profile_id: UUID,
    job_id: UUID,
    session: AsyncSession,
) -> MatchResult | None:
    candidate = await load_candidate_snapshot(
        profile_id,
        session,
    )

    if candidate is None:
        return None

    job = await load_job_snapshot(
        job_id,
        session,
    )

    if job is None:
        return None

    requirements = [
        {
            "requirement_type": requirement.requirement_type,
            "text": requirement.text,
            "importance": requirement.importance,
            "skills": requirement.skills,
        }
        for requirement in job.requirements
    ]

    return match_candidate_to_job(
        candidate_skills=candidate.skills,
        required_skills=job.required_skills,
        requirements=requirements,
    )